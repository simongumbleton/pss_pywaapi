#import pss_pywaapi.pss_pywaapi as pss_pywaapi
#import pss_helpers as p
import pss_pywaapi


print(dir(pss_pywaapi))

res = pss_pywaapi.connect()
#res = p.connect()
print(res)

pss_pywaapi.exit()

exit()