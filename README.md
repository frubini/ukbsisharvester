# ukbsisharvester

This script extract data from Narcis API

# Dependencies

## PYOAI
This project makes use of https://github.com/infrae/pyoai/, the library is dirctly added to this source code  (commit 4800af53b2ed096a0305eed1d6710138a65eabcd 8/3/22)  


# Installation :

1. Clone the repository
2. install **pip** end **pipenv** 
3. run the following commands:
4. cd to/you/project/dir/
5. run `pipenv install` 
6. run `pipenv shell`
7. Configure the relevant options in the config.py file

# Customization

if you need different metadata modify the function: **get_client()** in harvest.py

# Running the harvester

You can run the harvest task by modifying the **main()** function of harvest.py and then run `python harverst.py`
You can run one of the scripts without arguments:
- **harvest_initial.py**: to run the initial harvest until today @00:00, you can modify the start date in the script
- **harvest_daily.py**: to run the harvest only from yesterday
- **harvest_count.py**: it extracts the amount of articles from the filter menu Narcis website (only document type articles )







