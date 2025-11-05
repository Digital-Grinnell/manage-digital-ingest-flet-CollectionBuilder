#!/bin/bash

# Alma AWS S3 Upload Script
# This script helps upload files from the temporary directory to Alma's AWS S3 storage
# Replace <profile-id> and <import-id> with values from the Alma Digital Uploader

# Step 1: Print the name and contents of the upload bucket
echo "Step 1: Listing contents of Alma S3 upload bucket..."
aws s3 ls s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/ --recursive

echo ""
echo "Copy/paste the '/<profile-id>/<import-id>/' portion from the output above"
echo "Then edit this script and replace <profile-id> and <import-id> in the commands below"
echo ""
read -p "Press Enter when ready to continue with the copy command..."

# Step 2: Copy files from temporary directory to S3
# NOTE: Replace {temp_directory} with actual path from page.session.temp_directory
# NOTE: Replace <profile-id> and <import-id> with values from Step 1
echo ""
echo "Step 2: Copying files to Alma S3 storage..."
aws s3 cp {temp_directory}/OBJS/ s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/<profile-id>/<import-id>/ --recursive

# Step 3: Verify the upload
echo ""
echo "Step 3: Verifying upload..."
aws s3 ls s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/ --recursive

echo ""
echo "Once verified, return to Alma to complete the import operation"
