import sys
import os
import re
import math

sys.path.append('..')

from waapi import WaapiClient
from pprint import pprint
from pss_helpers import soundbank_helper
from pss_helpers import Files
import operator
from pss_helpers import wwise_settings

client = None


EventActionIDs = {
#https://www.audiokinetic.com/fr/library/edge/?source=SDK&id=wwiseobject_action.html
    "Play":1,
    "Stop":2,
    "StopAll":3,
    "Pause":7,
    "PauseAll":8,
    "Resume":9,
    "ResumeAll":10,
    "Break":34,
    "Seek":36,
    "SeekAll":37,
    "PostEvent":41
}

def getWwiseUserSetting_WAMPport():
    """Get the WAMP port saved in the user setting file for the authoring tool"""
    return wwise_settings.get_wamp_port()

def getWwiseUserSettingByName(Name=""):
    """ Get a named setting from the various .wsettings files wwise generates.
    Wsetting files contain setting dictionaries that look like this.........
    DefaultOutputBus Name='SFX' ID='{DA827D60-6AFF-47BB-AB1B-BD786FCFD3E6}'...or....
    Property Name='Waapi\WampPort' Type='int32' Value='8095'.

    :param Name: Name of the setting to retrieve
    :return: Dictionary of Key Value pairs relating to the requested setting, or None if not found

    """
    if not Name:
        return None
    DirsToCheck = []
    DirsToCheck.append(wwise_settings.get_wwise_datadir())
    DirsToCheck.append(getPathToWwiseProjectFolder())
    return wwise_settings.get_wwise_usersetting(Name,DirsToCheck)


def getWwiseVersion():
    """Get the Wwise Version struct"""
    result = client.call("ak.wwise.core.getInfo")
    if result:
        return result["version"]
    else:
        return False

def checkWwiseVersionIsAtLeast(year=2019,major=0,minor=0,build=0):
    """ Check the wwise version is at least equal to the version required
    For version info see https://www.audiokinetic.com/en/library/edge/?source=SDK&id=ak_wwise_core_getinfo.html
    :param year: The year element of the wwise version
    :param major: The major element of the wwise version
    :param minor: The minor element of the wwise version
    :param build: The build element of the wwise version
    :return: True if the wwise version is equal or greater than the input, otherwise False
    """
    version = getWwiseVersion()
    if not version:
        print("Error getting wwise version")
        return False
    return version["year"] >= year and version["major"] >= major and version["minor"] >= minor and version["build"] >= build


def connect(port = None):
    """ Connect to Wwise authoring api , on the port provided. If port is left empty, we try to read the port set in the user preferences settings file.
    If port is empty and the user settings file cannot be read, default port to use is 8080
    This sets up the client used for all future calls in the same session, so should be called before any other functions

    :param port: The waapi port to use (default is 8080 if not provided, and user settings cannot be read)
    :return: wwise connection info structure OR False

    """
    if not port:
        port = getWwiseUserSetting_WAMPport()
        if not port:
            port = 8080

    global client
    try:
        client = WaapiClient(url="ws://127.0.0.1:{0}/waapi".format(port))
    except Exception as ex:
        print("Connection error: {}".format(ex))
        print("Error connecting to Wwise. Please check your Waapi settings in User Preferences (usually wrong wamp port) .....exiting")
        #input('Press <ENTER> to continue')
        return False
        #sys.exit()
    else:
        result = client.call("ak.wwise.core.getInfo")
        return result

def exit():
    """Exiting the connection. Also clears automation mode

    """
    automationMode(False)
    try:
        client.disconnect()
    except Exception as ex:
        print("call error: {}".format(ex))
        return False

def getClient():
    """Getter for the waapi client connection

    """
    return client

def call(procedure,arguments):
    """Support manually calling a waapi procedure with custom arguments

    :param procedure: The name of the waapi procedure to call
    :param arguments: The argument map to pass to procedure

    :return: Result structure or False

    """
    try:
        res = client.call(procedure,arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

############# Function definitions #########################################

### Project undo and save ######

def beginUndoGroup():
    """Begin an undo group

    """
    try:
        res = client.call("ak.wwise.core.undo.beginGroup")
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def cancelUndoGroup():
    """Cancel an undo group

        """
    try:
        res = client.call("ak.wwise.core.undo.cancelGroup")
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def endUndoGroup(undogroup):
    """Name and end an undo group

    :param undogroup: Name to give the undo group that is ending

    """
    undoArgs = {"displayName": undogroup}
    try:
        res = client.call("ak.wwise.core.undo.endGroup", undoArgs)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def saveWwiseProject():
    """Save the wwise project

    """
    try:
        res = client.call("ak.wwise.core.project.save")
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def setupSubscription(subscription, target, returnArgs = ["id", "name", "path"]):
    """Subscribe to an event. Define a target to call when triggered, get the retunArgs back

    :param subscription: Waapi subscription topic
    :param target: The function to run on the callback trigger
    :param returnArgs: Properties to return with the callback

    """
    try:
        res = client.subscribe(subscription, target, {"return": returnArgs})
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def getProjectInfo(additionalProperties=[]):
    """Get the wwise project info by default returns filePath, @DefaultLanguage

    :param additionalProperties: List of additional properties to return from the project (optional)
    :return: Results structure or False

    """
    arguments = {
        "from": {"ofType": ["Project"]},
        "options": {
            "return": ["type","id", "name", "filePath","@DefaultLanguage"]+additionalProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get",arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None and len(res["return"]) > 0:
            return res["return"][0]
        else:
            return False

def getLanguages():
    """Get the list of languages from the wwise project

    :return: List of languages

    """
    langlist=[]
    arguments = {
        "from": {"ofType": ["Language"]},
        "options": {
            "return": ["name"]
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            for lang in res["return"]:
                if lang['name'] != 'SFX' and lang['name'] != 'External' and lang['name'] != 'Mixed':
                    langlist.append(lang['name'])
            return langlist
        else:
            return []

def getPathToWwiseProjectFolder():
    """Gets a path to the root folder of wwise project, cleans any nonsense from Mac paths.

    :return: os.path formated path to the wwise folder on disk

    """
    projectInfo = getProjectInfo()
    WwiseProjectPath = projectInfo["filePath"]
    WwiseProjectPath = WwiseProjectPath.replace("Y:", "~").replace('\\', '/')
    pathToWwiseFolder = os.path.expanduser(os.path.dirname(WwiseProjectPath))
    return pathToWwiseFolder


###  Object creation and property setting ######
def createWwiseObject(parentID, otype="BlendContainer", oname="", conflict="merge"):
    """Create a wwise object of type otype, called oname, underneath

    :param parentID: The GUID of the parent object
    :param otype: The type of wwise object to create
    :param oname: The name to give the new object
    :param conflict: Behaviour for conflicting objects (default=merge)

    :return: The newly created wwise object structure or False

    """
    createObjArgs = {
        "parent": parentID,
        "type": otype,
        "name": oname,
        "onNameConflict": conflict
    }
    try:
        res = client.call("ak.wwise.core.object.create", createObjArgs)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def createWwiseObjectFromArgs(args = {}):
    """Create a wwise object from a custom argument structure.
    Useful if you need to create many complex objects.

    :param args: A map of custom arguments for ak.wwise.core.object.create
    :return: The newly created wwise object(s) or False

    """
    try:
        res = client.call("ak.wwise.core.object.create", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def getPropertyAndReferenceNamesForObject(ObjIDorPath=None,classid=None):
    """Retrieves the list of property and reference names for an object.

    :param ObjIDorPath: The ID (GUID), name, or path of the object
    :param classid: The class ID to use instead of a specific object
    :return: The names of properties and references for the object type

    """
    if not ObjIDorPath and not classid:
        return False
    args = {}
    if classid:
        args = {
            "classid": classid
        }
    else:
        args = {
            "object": ObjIDorPath
        }
    try:
        res = client.call("ak.wwise.core.object.getPropertyAndReferenceNames", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def setWwiseObjectWithArgs(args = {}):
    """Set or create wwises object from a custom argument structure.
    Useful if you need to create many complex objects. See ak.wwise.core.object.set in wwise docs
    Only supported in Wwise 2022 and higher

    :param args: A map of custom arguments for ak.wwise.core.object.create
    :return: The newly created or modified wwise object(s) or False

    """
    if not checkWwiseVersionIsAtLeast(2022):
        print("This feature is only supported in Wwise 2022 and higher")
        return False
    try:
        res = client.call("ak.wwise.core.object.set", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def pasteObjectProperties(source=None,targets=[],pasteMode="replaceEntire",inclusion=[],exclusion=[]):
    """Pastes properties, references and lists from one object to any number of target objects.
    See https://www.audiokinetic.com/en/library/edge/?source=SDK&id=ak_wwise_core_object_pasteproperties.html
    Only supported in Wwise 2022 and higher

    :param source: The ID, name, or path of the source object.
    :param targets: A list of the target objects (The ID, name, or path of the target object)
    :param pasteMode: Paste mode for lists. Default value is "replaceEntire". With "replaceEntire" all elements in the lists of a target object are removed and all selected elements from the source's lists are copied.
    :param inclusion: Array of properties, references and lists to include in the paste operation. When not specified, all properties, references and lists are included, and the exclusion defines which ones to exclude
    :param exclusion: Array of properties, references and lists to exclude from the paste operation. When not specified, no properties, references and lists are excluded.
    :return: The result structure or False

    """
    if not checkWwiseVersionIsAtLeast(2022):
        print("This feature is only supported in Wwise 2022 and higher")
        return False
    if not source or not targets:
        print("Missing required arguments to pasteObjectProperties")
        return False
    args = {
        "source": source,
        "targets": targets,
        "pasteMode": pasteMode,
        "inclusion": inclusion,
        "exclusion": exclusion
    }
    try:
        res = client.call("ak.wwise.core.object.pasteProperties", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res


def createControlInputStructForNewModulator(type = "ModulatorTime",name = "New Modulator",AdditionalKeyValueProperties = {}):
    """Helper function to create a ControlInputStruct for use with setCreateRTPCCurveForObject()
    See ak.wwise.core.object.set in wwise docs

    :param type: The type of modulator to be created. Possible values: ModulatorLfo, ModulatorEnvelope, ModulatorTime,GameParameter,MidiParameter
    :param name: The name of the modulator to be created
    :param AdditionalKeyValueProperties: A dictionary of additional control properties to set for a modulator e.g. for ModulatorTime this might be: {"@TimeModDuration": 5,"@EnvelopeStopPlayback": false}

    :return: The newly created or modified wwise object(s) or False

    """
    if not type or not name:
        return {}
    args = {
        "type": type,
        "name": name,
    }
    for k,v in AdditionalKeyValueProperties:
        args[k] = v
    return args


def setCreateRTPCCurveForObject(ObjIDOrPath, PropertyName, ControlInputStructOrID = None, PointsList=None):
    """Set or create an RTPC curve on an object
    See ak.wwise.core.object.set in wwise docs
    Only supported in Wwise 2022 and higher

    :param ObjIDOrPath: The ID or path of the object which will have the new RTPC curve
    :param PropertyName: The name of the property to be controlled (e.g. OutputBusVolume)
    :param ControlInputStructOrID: A struct defining the control input. Either can be the ID of an existing RTPC curve, or a struct creating a new modulator, filled by createControlInputStructForNewModulator()
    :param PointsList: List of points for the new curve, in the format [{ "x": 100.0, "y": -20.82785, "shape": "Linear" },{ "x": 10000.0, "y": 21.8509, "shape": "Linear" }]
    :return: The newly created or modified wwise object(s) or False

    """
    if not checkWwiseVersionIsAtLeast(2022):
        print("This feature is only supported in Wwise 2022 and higher")
        return False
    if PointsList is None:
        PointsList = [{"x": 0, "y": 0, "shape": "Linear"}, {"x": 100, "y": 0, "shape": "Linear"}]
    if ControlInputStructOrID is None:
        ControlInputStructOrID = createControlInputStructForNewModulator()
    if not ObjIDOrPath or not PropertyName or not ControlInputStructOrID:
        print("ERROR! One or more missing arguments to setCreateRTPCCurveForObject")
        return False

    args = {
        "objects": [
            {
                "object": ObjIDOrPath,
                "@RTPC": [
                    {
                        "type": "RTPC",
                        "name": "",
                        "@Curve": {
                            "type": "Curve",
                            "points": PointsList
                        },
                        "@PropertyName": PropertyName,
                        "@ControlInput": ControlInputStructOrID
                    }
                ]
            }
        ]
    }
    return setWwiseObjectWithArgs(args)


def getRTPCCurvesForObject(ObjIDOrPath):
    """Get the RTPC curves for an object
    See https://www.audiokinetic.com/en/library/edge/?source=SDK&id=wwiseobject_rtpc.html
    Only supported in Wwise 2022 and higher

    :param ObjIDOrPath: The ID or path of the object
    :return: The list of RTPC curve structs for the input object

    """
    if not checkWwiseVersionIsAtLeast(2022):
        print("This feature is only supported in Wwise 2022 and higher")
        return False
    if not ObjIDOrPath:
        return False
    res = None
    if isStringValidID(ObjIDOrPath):
        res = getObjectProperties(ObjIDOrPath,["@RTPC"])
    else:
        res = getObjectProperties(ObjIDOrPath, ["@RTPC"],tfrom="path")
    return res.get("@RTPC",False)

def createEventForObject(objectID,EventParent,action="Play",eventName="",conflictmode="merge"):
    """Create an event targeting a given object,
    with overloaded arguments for event name and action.

    :param objectID: The GUID of the object to be targeted by the event
    :param EventParent: A GUID or path of an object to be the parent of the new event. If a path which doesnt exist it will be created

    :param action: Named argument. The action type of the event. Defaults to Play
    :param eventName: Named argument. The name of the event. If not provided, the event will be named based on the action + object name
    :param conflictmode: Named argument. What to do in the event of a name conflict
    :return: The newly created wwise object(s) or False

    """

    if not objectID or not EventParent:
        print("Error: Missing required argument(s)")
        return False

    isParentID = isStringValidID(EventParent)
    targetObject = getObjectProperties(objectID)
    parentObject = None
    if isParentID:
        parentObject = getObjectProperties(EventParent)
    else:
        if "\\Events" in EventParent:
            EventParent = str.lstrip(EventParent,"\\Events")
        elif "Events" in EventParent:
            EventParent = str.lstrip(EventParent,"Events")
        parentObject = createStructureFromPath(EventParent,"\\Events")

    Name = ""
    if eventName == "":
        Name = action + "_" + targetObject["name"]
    else:
        Name = eventName


    actiontype = EventActionIDs.get(action)
    if not actiontype:
        print("Error: Unsupported action argument: "+action)
        return False

    args = {
        "parent":parentObject["id"],
        "type":"Event",
        "name":Name,
        "onNameConflict":conflictmode,
        "children":[
            {
                "name":"",
                "type":"Action",
                "@ActionType":actiontype,
                "@Target":targetObject["id"]
            }
        ]

    }

    try:
        res = client.call("ak.wwise.core.object.create", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def setProperty(objectID, property, value,platform=None):
    """Set a property of a wwise object

    :param objectID: GUID of the object
    :param property: Name of the property to set
    :param value: The value to set for given property
    :param platform: Optional. The platform to apply the property for
    :return: Result structure or False

    """
    setPropertyArgs = {
        "object": objectID,
        "property": property,
        "value": value
    }
    if platform:
        setPropertyArgs["platform"]=platform
    try:
        res = client.call("ak.wwise.core.object.setProperty",setPropertyArgs)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def setPropertyPerPlatform(object, property, value, platform):
    """Set a property of a wwise object

    :param object: GUID of the object
    :param property: Name of the property to set
    :param value: The value to set for given property
    :param platform: The platform to apply this property to
    :return: Result structure or False

    """
    setPropertyArgs = {
        "object": object,
        "property": property,
        "value": value,
        "platform": platform
    }
    try:
        res = client.call("ak.wwise.core.object.setProperty",setPropertyArgs)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def setReference(objectID, reference, value,platform=None):
    """Set a reference of a wwise object

    :param objectID: GUID of the object
    :param reference: Name of the reference to set
    :param value: The value to set for given property
    :param platform: Optional. The platform to apply the reference for
    :return: Result structure or False

    """
    setArgs = {
        "object": objectID,
        "reference": reference,
        "value": value
    }
    if platform:
        setArgs["platform"]=platform
    try:
        res = client.call("ak.wwise.core.object.setReference",setArgs)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def setNotes(objectID, value):
    """Set the notes of object to value

    :param objectID: GUID of the object
    :param value: String to set as notes
    :return: Result structure or False

    """
    setPropertyArgs = {
        "object": objectID,
        "value": value
    }
    try:
        res = client.call("ak.wwise.core.object.setNotes",setPropertyArgs)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def importAudioFiles(args):
    """Import audio files with custom args

    :param args: A map of custom arguments for ak.wwise.core.audio.import
    :return: Result structure or False

    """
    try:
        res = client.call("ak.wwise.core.audio.import", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def importAudioFilesBatched(args,size = 100):
    """Import audio files with custom args. Splits large import jobs into batches of *size* (waapi has issues parsing large import jobs)

    :param args: A map of custom arguments for ak.wwise.core.audio.import
    :param size: size of the batches to import (defaults to 100)
    :return: Result structure or False

    """
    results = ""
    importList = args["imports"]
    count = len(importList)
    div = count / size

    for batch in Files.splitListIntoNchunks(importList, math.ceil(div)):

        args["imports"] = batch

        try:
            res = client.call("ak.wwise.core.audio.import", args)
        except Exception as ex:
            print("call error: {}".format(ex))
            return False
        else:
            if results == "":
                results = res
            else:
                if "objects" in res and "objects" in results:
                    existing = results["objects"]
                    new = res["objects"]
                    combined = existing + new
                    results["objects"] = combined

    return results

def setupImportArgs(parentID, fileList,originalsPath,language="SFX"):
    """Helper function to construct args for import operation

    :param parentID: GUID of the parent object
    :param fileList: List of audio files to import
    :param originalsPath: Relative location to put new files inside Originals
    :param language: Import audio as SFX (default) or a given language
    :return: An arguments structure ready to be passed into importAudioFiles()

    """
    ParentID = str(parentID)
    importFilelist = []
    if language != "SFX":
        type = "<Sound Voice>"
    else:
        type = "<Sound SFX>"

    for audiofile in fileList:
        foo = audiofile.rsplit('.') #remove extension from filename
        audiofilename = foo[0]
        importFilelist.append(
            {
                "audioFile": audiofile,
                "objectPath": type + os.path.basename(audiofilename)
            }
        )

    importArgs = {
        "importOperation": "useExisting",
        "autoAddToSourceControl": True,
        "default": {
            "importLanguage": language,
            "importLocation": ParentID,
            "originalsSubFolder": originalsPath
            },
        "imports": importFilelist
        }
    return importArgs


def deleteWwiseObject(objectID):
    """Delete a wwise object

    :param objectID: GUID of object to be deleted
    :return: Result structure or False

    """
    args = {"object":objectID}
    try:
        res = client.call("ak.wwise.core.object.delete",args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

###  Searching the project  ######

def getSelectedObjects(properties=[]):
    """Get the currently selected object(s), returning any extra properties.
    By default objects will return ["id","type", "name", "path"] + properties[]

    :param properties: list of additional properties to be returned for the wwise objects.
    :return: Result structure or False

    """
    baseProperties = ["id","type", "name", "path"]
    selectedObjectArgs = {
        "options": {
            "return": baseProperties+properties
        }
    }
    try:
        res = client.call("ak.wwise.ui.getSelectedObjects",selectedObjectArgs)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            return res["objects"]
        else:
            return []

def getDescendantObjectsOfType(objectID,ofType,returnProperties=[],tfrom="id",select="descendants"):
    """Perform a search fromObject to find descendants ofType, return additional properties for each object.
    Optionally change the from and select parts of the query, by default use ID as the object
    for more info on options see Wwise SDK for ak.wwise.core.object.get
    https://www.audiokinetic.com/library/edge/?source=SDK&id=ak_wwise_core_object_get.html

    :param objectID: Starting point of search. Default is a GUID
    :param ofType: Type of wwise objects to search for
    :param returnProperties: Additional properties to return for each object
    :param tfrom: Key that determines how fromObject is used in the search (default=id)
    :param select: Key that determines which objects are searched in relation to the fromObject (default=descendants)
    :return: Result structure or False

    """
    baseProperties = ["id","type", "name", "path"]
    arguments = {
        "from": {tfrom: [objectID]},
        "transform": [
            {"select": [select]},
            {"where":["type:isIn",[ofType]]}
        ],
        "options": {
            "return": baseProperties+returnProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            return res["return"]
        else:
            return []

def getDescendantObjects(objectID,returnProperties=[],tfrom="id",select="descendants"):
    """Perform a search fromObject to find all descendants, return additional properties for each object.
    Optionally change the from and select parts of the query, by default use ID as the object

    :param objectID: Starting point of search.
    :param returnProperties: Additional properties to return for each object
    :param tfrom: Key that determines how fromObject is used in the search (default=id)
    :param select: Key that determines which objects are searched in relation to the fromObject (default=descendants)
    :return: Result structure or False

    for more info on options see Wwise SDK for ak.wwise.core.object.get
    https://www.audiokinetic.com/library/edge/?source=SDK&id=ak_wwise_core_object_get.html

    """
    baseProperties = ["id","type", "name", "path"]
    arguments = {
        "from": {tfrom: [objectID]},
        "transform": [
            {"select": [select]}
        ],
        "options": {
            "return": baseProperties+returnProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            return res["return"]
        else:
            return []


def getObjectsByName(name,type,returnProperties=[],tfrom="ofType"):
    """Perform a search by name, return additional properties for each object.
    Named search must also include a type filter.
    For more info on options see Wwise SDK for ak.wwise.core.object.get
    https://www.audiokinetic.com/library/edge/?source=SDK&id=ak_wwise_core_object_get.html

    :param name: String to match with object names
    :param type: Type of wwise objects to search for
    :param returnProperties: Additional properties to return for each object
    :param tfrom: Key that determines how fromObject is used in the search (default=ofType)
    :return: Result structure or False

    """
    baseProperties = ["id","type", "name", "path"]
    arguments = {
        "from": {tfrom: [type]},
        "transform": [
            #{"where": ["name:matches",[name]]}
            {"where": ['name:matches', '^'+name+'$']}
        ],
        "options": {
            "return": baseProperties+returnProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            return res["return"]
        else:
            return []

def searchForObject(searchterm,returnProperties=[],tfrom="search"):
    """Perform a search by name, return additional properties for each object.
    For more info on options see Wwise SDK for ak.wwise.core.object.get
    https://www.audiokinetic.com/library/edge/?source=SDK&id=ak_wwise_core_object_get.html

    :param searchterm: String to search for
    :param returnProperties: Additional properties to return for each object
    :param tfrom: Type of search to do, defaults to "search" can be overridden to use path
    :return: Result structure or False

    """
    baseProperties = ["id","type", "name", "path"]
    arguments = {
        "from": {tfrom: [searchterm]},
        "options": {
            "return": baseProperties+returnProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            return res["return"]
        else:
            return []

def getObjectProperties(objectID,returnProperties=[],tfrom="id"):
    """Get some additional properties from a wwise Object, by default use ID as the object

    :param objectID: Wwise object to get properties from. Default is a GUID
    :param returnProperties: Additional properties to return for each object
    :param tfrom: Key that determines how fromObject is used in the search (default=id)
    :return: Result structure or False
    for more info on options see Wwise SDK for ak.wwise.core.object.get
    https://www.audiokinetic.com/library/edge/?source=SDK&id=ak_wwise_core_object_get.html

    """
    baseProperties = ["id","type", "name", "path"]
    arguments = {
        "from": {tfrom: [objectID]},
        "transform": [],
        "options": {
            "return": baseProperties+returnProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None and len(res["return"])>0:
            if len(res["return"]) > 1:
                return res["return"]
            else:
                if len(res["return"]) > 0:
                    return res["return"][0]
                else:
                    return False
        else:
            return []

def getAllObjectsOfType(ofType,returnProperties=[]):
    """Get all objects of a certain type, and return any extra properties

    :param ofType: Type of wwise objects to search for
    :param returnProperties: Additional return properties to get for each object
    :return: Result structure or False

    """
    baseProperties = ["id","type", "name", "path"]
    arguments = {
        "from": {"ofType": [ofType]},
        "transform": [
            #{"select": "parent"}
        ],
        "options": {
            "return": baseProperties+returnProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            return res["return"]
        else:
            return []

def getReferencesToObject(objectID,returnProperties=[],tfrom="id"):
    """ get the references to a given object, by default use ID as the object

    :param fromObject: Wwise object to get references to. Default is a GUID
    :param returnProperties: Additional properties to return for each object
    :param tfrom: Key that determines how fromObject is used in the search (default=id)
    :return: Results structure or False

    """
    baseProperties = ["id","type", "name", "path"]
    arguments = {
        "from": {tfrom: [objectID]},
        "transform": [
            {"select": ["referencesTo"]}
        ],
        "options": {
            "return": baseProperties+returnProperties
        }
    }
    try:
        res = client.call("ak.wwise.core.object.get", arguments)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        if res != None:
            return res["return"]
        else:
            return []

def getListOfTypes():
    """return the list of valid object types, can help debugging"""
    try:
        res = client.call("ak.wwise.core.object.getTypes")
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def filterWwiseObjects(objects,property,operation, value, NOT=0):
    """helper function to filter a list of objects by a specific property, value and comparison operation
    # e.g. return only objects with "@Volume" , "<" , "-48"

    :param objects: List of wwise objects to filter
    :param property: Which property to filter by
    :param operation: String comparison operator for filter. One of; "==","<","<=",">",">=","!=","contains"
    :return: List of objects matching filters
    """
    results = []
    op = getOperator(operation)
    for obj in objects:
        if not property in obj:## this object doesnt have the property, so skip it
            continue
        if NOT ==0:
            if op(obj[property],value):
                results.append(obj)
        else:
            if not op(obj[property],value):
                results.append(obj)
    return results

def getOperator(string):
    """Helper function to convert string comparison to python operator"""
    if string == "==":
        return operator.eq
    elif string == "<":
        return operator.lt
    elif string == "<=":
        return operator.le
    elif string == ">":
        return operator.gt
    elif string == ">=":
        return operator.ge
    elif string == "!=":
        return operator.ne
    elif string == "contains":
        return operator.contains
    else:
        print("WARNING!!! Did not recognise operator argument..defaulting to EQUALS")
        return operator.eq


#####  Soundbanks #####
def generateSoundbanks(banklist = []):
    """Generate soundbanks

    :param banklist: List of bank names to generate
    """
    args = {
        "command": "GenerateSelectedSoundbanksAllPlatforms",
        "objects": [
            banklist
        ]
    }
    try:
        res = client.call("ak.wwise.ui.commands.execute", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def getSoundbanks(objectID,tfrom="id"):
    """ Return all Soundbanks referencing any object of the Work Unit directly

    :param objectID: The object GUID to use in the search
    :param tfrom: Key that determines how obj is used in the search (default=id)
    :return: List of banks directly referencing obj
    """
    BankList =[]
    for transform in soundbank_helper.bankTransforms:
        arguments = {
            "from": {tfrom: [objectID]},
            "transform": transform,
            "options": {
                "return": ['id', 'name', 'type']
            }
        }
        try:
            res = client.call("ak.wwise.core.object.get", arguments)
        except Exception as ex:
            print("call error: {}".format(ex))
            return False
        else:
            if res != None:
                # print (res.kwresults["return"])
                for bank in res["return"]:
                    if bank["name"] not in BankList:
                        BankList.append((bank["name"]))
    return BankList


def executeCommand(command,objects = []):
    """wrapper to execute UI commands
    See https://www.audiokinetic.com/library/2017.1.9_6501/?source=SDK&id=globalcommandsids.html

    :param command: Command to execute
    :param objects: List of objects to pass to the command
    :return: Result structure or False
    """
    args = {}
    if type(objects) is list:
        args = {
            "command": command,
            "objects": objects
        }
    else:
        args = {
            "command": command,
            "objects": [
                objects
            ]
        }
    try:
        res = client.call("ak.wwise.ui.commands.execute", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def automationMode(enabled):
    """set automation mode on/off

    :param enabled: True or False

    :return: Result struct or False

    """
    args = {
        "enable": enabled
    }
    try:
        res = client.call("ak.wwise.debug.enableAutomationMode", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def checkoutWorkUnit(workunitID):
    """Source control operation to check out work unit

    :param workunitID: GUID of the work unit to checkout
    :return: Result structure or False
    """
    return executeCommand("WorkgroupCheckoutWWU",workunitID)

def cleanfilePathFromWwise(path):
    """Cleans the undesired characters from Mac paths that Wwise gives you. E.g. replaces Y: with ~

    :param path: path to clean (e.g. wproj or work unit path)
    :return: os.path formated path, cleaned of Mac/WINE characters
    """
    cleanMacpath = path.replace("Y:","~").replace('\\', '/')
    return os.path.abspath(os.path.expanduser(cleanMacpath))

def showObjectsInListView(objects = []):
    """Open the provided list of objects in the Wwise List View

    :param objects: A List of object IDs, paths or type qualified names
    :return: Result structure or False
    """
    try:
        res = executeCommand("ShowListView",objects)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def setSwitchContainerAssignment(switch,child):
    """Assign a given child object to a given switch (switch container)

    :param switch: Name of the switch to assign child to
    :param child: ID of the wwise object to assign to switch
    :return: Result structure or False
    """
    args = {
        "stateOrSwitch": switch,
        "child":child
    }
    try:
        res = client.call("ak.wwise.core.switchContainer.addAssignment", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def removeSwitchContainerAssignment(switch,child):
    """Remove a given child object from a given switch (switch container)

    :param switch: Name of the switch to assign child to
    :param child: ID of the wwise object to assign to switch
    :return: Result structure or False
    """
    args = {
        "stateOrSwitch": switch,
        "child":child
    }
    try:
        res = client.call("ak.wwise.core.switchContainer.removeAssignment", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def moveWwiseObject(objectID,parent, conflict="replace"):
    """move object to new location under parent

    :param objectID: ID of wwise object to move
    :param parent: ID of the parent to move object under
    :param conflict: Behaviour for conflicting objects (default = replace)
    :return: Result structure or False

    """
    args = {

        "object": objectID,
        "parent": parent,
        "onNameConflict": conflict
    }
    try:
        res = client.call("ak.wwise.core.object.move", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def renameWwiseObject(objectID,newName):
    """Rename a given object with newName

    :param objectID: ID of wwise object to rename
    :param newName: The new name of the wwise object
    :return: Result structure or False

    """
    args = {

        "object": objectID,
        "value": newName
    }
    try:
        res = client.call("ak.wwise.core.object.setName", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def copyWwiseObject(objectID, parent, conflict="replace"):
    """copy object to new location under parent
    
    :param objectID: ID of wwise object to copy
    :param parent: ID of the parent to paste object under
    :param conflict: Behaviour for conflicting objects (default = replace)
    :return: Result structure or False
    """
    args = {

        "object": objectID,
        "parent": parent,
        "onNameConflict": conflict
    }
    try:
        res = client.call("ak.wwise.core.object.copy", args)
    except Exception as ex:
        print("call error: {}".format(ex))
        return False
    else:
        return res

def isStringValidID(string):
    """Check if a given string is formatted as a valid ID, using regex fullmatch with pattern - ^\{[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}\}$

    :param string: The string to match against the regex ID pattern
    :return: True if string matches the pattern of a wwise ID, otherwise  False

    """
    IDRegExPattern = r"^\{[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}\}$"
    result = re.fullmatch(IDRegExPattern,string)
    if result:
        return True
    else:
        return False

def createStructureFromPath(path,parent):
    r"""Create a structure of objects from a string path and return the last object in the path. If the path already exists, no new objects are created, and the existing last object in the path is returned.

    :param path: String path of the structure to be created. Objects should be seperated by double backslash (\\\\\\\\) and type should prefix name in angle brackets <> e.g <WorkUnit>MyWorkUnit
    :param parent: ID or path of the parent object to create the structure under e.g. \\\\\\\\Actor-Mixer Hierarchy
    :return: The last descendent object in the path created

    e.g. res = pss_pywaapi.createStructureFromPath("<WorkUnit>Hello\\\\\\\\<Folder>World", "\\\\\\\\Actor-Mixer Hierarchy")

    If no types are provided, and elements of the path do not exist already, then default types will be used.
    Default types are first Folder then WorkUnit. If a Folder cannot be created at the given location (usually because there is no work unit in the path), then a Work Unit will be created.
    """
    
    #Above docstring needs so many backslashes for RST documentation display.. In python you should make sure to use double backslash (\\)
    # res = pss_pywaapi.createStructureFromPath("<WorkUnit>Hello\\<Folder>World", "\\Actor-Mixer Hierarchy")
    
    if not parent or not path:
        print("Error. Missing arguments")
        return False

    if path.startswith("\\Events\\"):
        path = path.replace("\\Events\\","\\",1)
    elif path.startswith("Events\\"):
        path = path.replace("Events\\", "\\",1)
    elif path.startswith("\\Actor-Mixer Hierarchy\\"):
        path = path.replace("\\Actor-Mixer Hierarchy\\", "\\",1)
    elif path.startswith("Actor-Mixer Hierarchy\\"):
        path = path.replace("Actor-Mixer Hierarchy\\", "\\",1)

    isParentID = isStringValidID(parent)
    if not isParentID:
        #the parent param was not an ID, lets try to find it in the wwise project
        if parent == "Actor-Mixer Hierarchy":
            parent = "\\"+parent
        elif parent == "Events":
            parent = "\\"+parent

        results = searchForObject(parent,[],"path")
        numOfResults = len(results)
        if numOfResults == 1:
            nextParentID = results[0]["id"]
        elif numOfResults == 0:
            print("Could not locate parent in wwise project. Attempting to create. Arg given = "+parent)
            if "Actor-Mixer Hierarchy" in parent:
                p = parent.partition("Actor-Mixer Hierarchy")[2]
                res = createStructureFromPath(p,"\\Actor-Mixer Hierarchy")
                if not res:
                    print("Error creating parent object")
                    return False
                nextParentID = res["id"]
            elif "Events" in parent:
                p = parent.partition("Events")[2]
                res = createStructureFromPath(p, "\\Events")
                if not res:
                    print("Error creating parent object")
                    return False
                nextParentID = res["id"]

        elif numOfResults > 1:
            print("Ambiguous parent argument. More than one possible parent found using arg: "+parent)
            print("Consider refining the argument or passing an explicit ID instead")
            return False
    else:
        result = searchForObject(parent,[],"id")
        if result:
            nextParentID = parent
        else:
            print("Error. Cannot find an object with matching ID from parent argument")
            return False


    lastChild = None
    pathlist = path.split("\\")
    for node in pathlist:
        if node == "":
            continue #skip empty nodes

        #get the name and type from the node
        type = ""
        name = ""
        if "<" in node:
            type = node.split(">")[0]
            type = type.replace("<", "")
            name = node.split(">")[1]
        else:
            type = None
            name = node

        # check if there is already a child with the name under the parent
        res = getDescendantObjects(nextParentID,[],"id","children")
        for item in res:
            if item["name"] == name:
                #node already exists in wwise
                nextParentID = item["id"]
                lastChild = item
                break
        else:
            if type:    #node contains a type, and we didn't find an existing item so we try to create it
                res = createWwiseObject(nextParentID,type,name)
                if res:
                    nextParentID = res["id"]
                    lastChild = res
                else:   #object was not created
                    print("Error! Could not create object and found no existing object named "+name+" underneath " + parent)
                    return False
            else:
                #No type was specified, and we didn't find an existing item - so try and create an item with a default type
                res = createWwiseObject(nextParentID, "Folder", name)
                if res:
                    nextParentID = res["id"]
                    lastChild = res
                else:  # object was not created as a default Folder, try creating it as a work unit instead
                    res2 = createWwiseObject(nextParentID, "WorkUnit", name)
                    if res2:
                        nextParentID = res2["id"]
                        lastChild = res2
                    else:
                        print("Error! Could not create object and found no existing object named " + name + " underneath " + parent)
                        return False

    if lastChild:
        return lastChild
    else:
        return False




############## End of Function definitions ##############################################

#If pywaapi is run as the main script, connect and print result
if __name__ == "__main__":
    result = connect()
    pprint(result)
    exit()

