#!/bin/bash

# Prompt user for year
read -p "Enter a year: " year

# Extract last two digits
last_two_digits="${year: -2}"

# Find all folders ending with the last two digits and zip them
matching_folders=$(find . -maxdepth 1 -type d -name "*$last_two_digits" | sed 's|^\./||' | grep -v '^\.$')

if [ -z "$matching_folders" ]; then
    echo "No folders found ending with $last_two_digits"
    exit 1
fi

echo "Found folders:"
echo "$matching_folders"

# Create zip file
zip -r "${year}.zip" $matching_folders

if [ $? -eq 0 ]; then
    echo "Successfully created ${year}.zip"
    
    # Ask user if they want to delete originals
    read -p "Do you want to delete the original folders? (y/n): " delete_choice
    
    if [ "$delete_choice" = "y" ] || [ "$delete_choice" = "Y" ]; then
        echo "$matching_folders" | xargs rm -rf
        echo "Original folders deleted"
    else
        echo "Original folders kept"
    fi
else
    echo "Failed to create zip file"
    exit 1
fi
