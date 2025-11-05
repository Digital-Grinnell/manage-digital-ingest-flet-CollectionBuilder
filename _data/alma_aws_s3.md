
# Suggested _aws s3..._ commands that should be used as part of the Alma-D operation

Assuming a CSV file was selected for import (not the FilePicker option), and that CSV file contains updated identifiers and filepaths, use these `aws s3` commands to complete an import...  

A new '{expanded_filename}' file has been populated for import.  The network path to this file in Finder will be "{constant.FINDER_PATH}/{collection}"

Now, use the 'Resources' menu and 'Digital Uploader' in Alma to submit '{expanded_filename}' for import. Then, use... `aws s3 ls s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/ --recursive`
to positively identify its COMPLETE path.  

Copy the ...01GCL_INST `/<PROFILE-ID>/<IMPORT-ID>/` portion of the path for use in subsequent steps.  

Edit and use this 'aws s3...' copy command, in concert with the Alma Digital Uploader, to copy files to AWS storage for ingest:"  

`aws s3 cp /Volumes/exports/OBJs/ s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/<PROFILE-ID>/<IMPORT-ID>/ --recursive`

Use this 'aws ls...' list command to check the status of files in AWS storage for ingest:" 

`aws s3 ls s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/ --recursive`

