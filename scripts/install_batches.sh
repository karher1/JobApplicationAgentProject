#!/bin/bash

# Job Application Agent - Batch Package Installation
# This script installs packages in logical batches

echo "🚀 Job Application Agent - Package Installation"
echo "Installing packages in batches..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment doesn't appear to be activated."
    echo "   It's recommended to activate your virtual environment first."
    read -p "   Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Function to install a batch
install_batch() {
    local file=$1
    local description=$2
    
    echo ""
    echo "=================================================="
    echo "Installing: $description"
    echo "File: $file"
    echo "=================================================="
    
    if [ -f "$file" ]; then
        if pip install -r "$file"; then
            echo "✅ Successfully installed: $description"
        else
            echo "❌ Failed to install: $description"
            return 1
        fi
    else
        echo "⚠️  Warning: $file not found, skipping..."
    fi
}

# Install batches
failed_batches=()

install_batch "requirements_core.txt" "Core Dependencies" || failed_batches+=("Core Dependencies")
install_batch "requirements_langchain.txt" "LangChain & AI Dependencies" || failed_batches+=("LangChain & AI Dependencies")
install_batch "requirements_selenium.txt" "Selenium & Web Automation" || failed_batches+=("Selenium & Web Automation")
install_batch "requirements_database.txt" "Database & Supabase Dependencies" || failed_batches+=("Database & Supabase Dependencies")

# Summary
echo ""
echo "=================================================="
echo "📋 INSTALLATION SUMMARY"
echo "=================================================="

if [ ${#failed_batches[@]} -eq 0 ]; then
    echo "✅ All packages installed successfully!"
else
    echo "❌ Failed batches: ${failed_batches[*]}"
    echo ""
    echo "To retry failed installations:"
    for batch in "${failed_batches[@]}"; do
        echo "   pip install -r requirements_${batch// /_//&/and}.txt"
    done
fi

echo ""
echo "🎉 Installation complete!"
echo "You can now run your job application automation script." 