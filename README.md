# Polygon/Point Overlap Detection Tool

The purpose of the tool is to detect when spatial point and polygon entries overlap for the same NID. A codebook is entered and (if applicable) a list of affected NIDs are returned along with infographs and actionable insights for analysts to use to remedy the issue. 

## Installing
Step 1. Install Conda
A powerful package manager and environment manager that you use with command line commands at the Anaconda Prompt for Windows, or in a Terminal window for macOS or Linux.
https://docs.anaconda.com/anaconda/install/

Step 2. Get Conda Running
Follow the sections Before you start, Contents, and starting conda. 
https://conda.io/docs/user-guide/getting-started.html

Step 3. Create Environment
Execute the below statement to set up the required package dependancies. Replace 'myenv' with whatever name you want for your new environment
```
conda create -n myenv python=3.5 geopandas=0.3.0 pandas=0.23.0 shapely=1.6.4 matplotlib=2.2.2 descartes=1.1.0 docopt=0.6.2 pillow=5.1.0
```
## Running the tool
//multiple use cases with example arguments? 

## Running the tests
//Explain how to run automated tests for this system
```
pytest enter
```
### Break down end to end tests
// Explain what these tests test and why
```
examples
```
