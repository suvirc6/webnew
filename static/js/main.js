document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');
    const promptButtons = document.querySelectorAll('.prompt-button');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const loadingIndicatorfullreport = document.getElementById('loadingIndicatorfullreport');
    const answerContainer = document.getElementById('answer');
    const initialMessage = document.getElementById('initialMessage');
    const customQueryInput = document.getElementById('customQueryInput');
    const customQueryButton = document.getElementById('customQueryButton');
    const generateReportButton = document.getElementById('generateReportButton');
    const downloadLink = document.getElementById('downloadLink');

    
    

    
    // Make sure loading is hidden on page load
    loadingIndicator.classList.add('hidden');
    
    // Show selected files when user selects them
    fileInput.addEventListener('change', function() {
        const fileCount = fileInput.files.length;
        if (fileCount > 0) {
            const fileNames = Array.from(fileInput.files).map(file => file.name).join(', ');
            uploadStatus.textContent = `${fileCount} file(s) selected: ${fileNames}`;
        } else {
            uploadStatus.textContent = '';
        }
    });
    
    // File upload functionality - updated for multiple files
    uploadButton.addEventListener('click', async function() {
        if (!fileInput.files.length) {
            uploadStatus.textContent = 'Please select at least one file first';
            return;
        }
        
        // Validate that all files are PDFs
        const invalidFiles = Array.from(fileInput.files).filter(file => 
            !file.name.toLowerCase().endsWith('.pdf')
        );
        
        if (invalidFiles.length > 0) {
            uploadStatus.textContent = `Invalid file types: ${invalidFiles.map(f => f.name).join(', ')}. Only PDF files are allowed.`;
            return;
        }
        
        const formData = new FormData();
        // Append each file with the parameter name 'files' (matching your backend)
        Array.from(fileInput.files).forEach(file => {
            formData.append('files', file);
        });
        
        uploadStatus.textContent = `Uploading ${fileInput.files.length} file(s)...`;
        uploadButton.disabled = true;
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                uploadStatus.textContent = `✅ ${result.status} - Files: ${result.filenames.join(', ')}`;
                // Enable prompt buttons after successful upload
                enablePromptButtons();
                // Enable custom query input after successful upload
                enableCustomQuery();
            } else {
                uploadStatus.textContent = `❌ Error: ${result.error || 'Upload failed'}`;
            }
        } catch (error) {
            uploadStatus.textContent = `❌ Error: ${error.message}`;
        } finally {
            uploadButton.disabled = false;
        }
    });
    
    // Enable prompt buttons
    function enablePromptButtons() {
        promptButtons.forEach(button => {
            button.disabled = false;
        });
    }
    
    // Enable custom query input
    function enableCustomQuery() {
        customQueryInput.disabled = false;
        customQueryButton.disabled = false;
    }
    
    // Handle prompt button clicks
    promptButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const promptKey = this.getAttribute('data-key');
            
            // Show loading indicator, hide other elements
            initialMessage.classList.add('hidden');
            answerContainer.classList.add('hidden');
            loadingIndicator.classList.remove('hidden');
            
            // Create form data for analysis request
            const formData = new FormData();
            formData.append('prompt_key', promptKey);
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                // Hide loading
                loadingIndicator.classList.add('hidden');
                
                if (response.ok) {
                    // Display answer - use innerHTML to render HTML tables
                    if (result.answer) {
                        answerContainer.innerHTML = result.answer;
                        answerContainer.classList.remove('hidden');
                    }
                } else {
                    answerContainer.textContent = `Error: ${result.error || 'Analysis failed'}`;
                    answerContainer.classList.remove('hidden');
                }
            } catch (error) {
                loadingIndicator.classList.add('hidden');
                answerContainer.classList.remove('hidden');
                answerContainer.textContent = `Error: ${error.message}`;
            }
        });
    });
    
    // Handle custom query button click
    customQueryButton.addEventListener('click', async function() {
        const query = customQueryInput.value.trim();
        
        if (!query) {
            answerContainer.textContent = "Please enter a question";
            answerContainer.classList.remove('hidden');
            initialMessage.classList.add('hidden');
            return;
        }
        
        // Show loading indicator, hide other elements
        initialMessage.classList.add('hidden');
        answerContainer.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');
        
        // Create form data for custom query request
        const formData = new FormData();
        formData.append('custom_query', query);
        
        try {
            const response = await fetch('/analyze_custom', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            // Hide loading
            loadingIndicator.classList.add('hidden');
            
            if (response.ok) {
                // Display answer - use innerHTML to render HTML tables
                if (result.answer) {
                    answerContainer.innerHTML = result.answer;
                    answerContainer.classList.remove('hidden');
                }
            } else {
                answerContainer.textContent = `Error: ${result.error || 'Analysis failed'}`;
                answerContainer.classList.remove('hidden');
            }
        } catch (error) {
            loadingIndicator.classList.add('hidden');
            answerContainer.classList.remove('hidden');
            answerContainer.textContent = `Error: ${error.message}`;
        }
    });
    
    // Allow Enter key to submit custom query
    customQueryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey && !customQueryButton.disabled) {
            e.preventDefault();
            customQueryButton.click();
        }
    });



// Generate report functionality
function enableGenerateReport() {
    generateReportButton.disabled = false;
}

uploadButton.addEventListener('click', () => {
    // after successful upload inside the try block
    enableGenerateReport();
});

generateReportButton.addEventListener('click', async () => {
    loadingIndicatorfullreport.classList.remove('hidden');
    answerContainer.classList.add('hidden');
    downloadLink.style.display = 'none';
    downloadLink.textContent = '';
    
    // Hide only the spinner, not the entire container
    const spinner = loadingIndicatorfullreport.querySelector('.spinner');

    try {
        const response = await fetch('/generate_report', { method: 'POST' });

        if (!response.ok) {
            const error = await response.json();
            answerContainer.textContent = `Error: ${error.error || "Failed to generate report"}`;
            answerContainer.classList.remove('hidden');
            loadingIndicatorfullreport.classList.add('hidden');
            return;
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = "equity_report_finlytic.docx";
        downloadLink.textContent = "Download Generated Report";
        downloadLink.classList.remove('hidden');
        downloadLink.style.display = 'inline-block';
        
        // Hide only the spinner, keep the container visible for the download link
        if (spinner) spinner.style.display = 'none';
    } catch (error) {
        answerContainer.textContent = `Error: ${error.message}`;
        answerContainer.classList.remove('hidden');
        loadingIndicatorfullreport.classList.add('hidden');
    }
});

});



