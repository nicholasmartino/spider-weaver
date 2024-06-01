import sys
from Local import BritishColumbia
from _Settings import regions
if 'win32' in sys.platform:
    drt = "C:/Users/nichmar.stu/Google Drive/Python"
else:
    drt = "/Volumes/Macintosh HD/Users/nicholasmartino/Google Drive/Python"

sys.path.insert(1, f"{drt}/urban-mobility")
from Analyst import Network
DIRECTORY = 'C:/Users/nichmar.stu/Google Drive/Databases/'

for key, value in regions.items():
    for city in value['British Columbia']:
        net = Network(f"{city}, British Columbia", directory=DIRECTORY)
        # net.update_databases()
    bc = BritishColumbia(cities=value['British Columbia'], directory=DIRECTORY)

    if 'win32' in sys.platform:
        BCA_DIR = 'S:/Research/eLabs/50_projects/16_PICS/07_BCA data'
    else:
        BCA_DIR = '/Volumes/SALA/Research/eLabs/50_projects/16_PICS/07_BCA data'

    bc.aggregate_bca_from_field(
        run=True, join=True, classify=True,  # BC Assessment
        inventory_dir=f'{BCA_DIR}/170811_BCA_Provincial_Data/Inventory Information - RY 2017 - Greater Vancouver.csv',
        geodatabase_dir=f'{BCA_DIR}/Juchan_backup/BCA_2017_roll_number_method/BCA_2017_roll_number_method.gdb')
