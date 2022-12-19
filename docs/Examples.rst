.. pss_pywaapi documentation master file, created by
   sphinx-quickstart on Wed Jun 17 18:43:53 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Examples
=======================================

Lets look at a few short examples of getting started using the module


***************
Getting sounds from the actor-mixer hierarchy
***************
This example demonstrates getting a list of sounds in the actor mixer hierarchy, and if the included flag is set, print the name of the sound.

.. code-block:: python

   import pss_pywaapi
   
   pss_pywaapi.connect()
   Sounds = pss_pywaapi.getDescendantObjectsOfType("\\Actor-Mixer Hierarchy", "Sound", ["@Inclusion"], "path")
   for sound in Sounds:
    if sound["@Inclusion"] == True:
       print(sound["name"])


***************
Setting properties
***************
This example demonstrates setting the volume property on the currently selected objects

.. code-block:: python

   import pss_pywaapi
   
   pss_pywaapi.connect()
   Selection = pss_pywaapi.getSelectedObjects()
   for object in Selection:
      pss_pywaapi.setProperty(object["id"],"@Volume", -6)


***************
Basic Importing of Audio
***************
This example demonstrates importing a list of new audio files into wwise under the first selected object

.. code-block:: python

   import pss_pywaapi


   ListOfAudioFiles = [] #Imagine a list of .wav files go here :)
   pss_pywaapi.connect()
   Selection = pss_pywaapi.getSelectedObjects()
   Parent = Selection[0]
   args = pss_pywaapi.setupImportArgs(Parent["id"],ListOfAudioFiles,"MyNewSounds","SFX")
   result = pss_pywaapi.importAudioFiles(args)
   print(result)
   

***************
Going Further
***************
A selection of example scripts can be found on the pss_pywaapi github, demonstrating use of the module in a few more advanced, real world scenarios
https://github.com/simongumbleton/pss_pywaapi/tree/master/Examples


