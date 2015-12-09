begin program.
import STATS_OPEN_PROJECT
reload(STATS_OPEN_PROJECT)
end program.

dataset close all.
new file.


STATS OPEN PROJECT FILE="c:/cc/misc2/extensions/python/stats_open_project/tests/projectÁ.txt".



STATS OPEN PROJECT FILE=="c:/cc/misc2/extensions/python/stats_open_project/tests/projectÁ.txt"   STARTUP=SET.


STATS OPEN PROJECT FILE="C:\cc\misc2\extensions\python\STATS_OPEN_PROJECT\tests\employee.txt"
    STARTUP=DELETE.

STATS OPEN PROJECT FILE="C:\cc\misc2\extensions\python\STATS_OPEN_PROJECT\tests\employee.txt"   
    STARTUP=SET.

STATS OPEN PROJECT FILE="C:\cc\misc2\extensions\python\STATS_OPEN_PROJECT\tests\employeeÁÁÁ.txt"   
    STARTUP=SET.

STATS OPEN PROJECT FILE="C:\cc\misc2\extensions\python\STATS_OPEN_PROJECT\tests\employeeÁÁÁ.txt"
    STARTUP=ASIS.
