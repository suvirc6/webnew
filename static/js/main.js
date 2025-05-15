document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');
    const promptButtons = document.querySelectorAll('.prompt-button');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const answerContainer = document.getElementById('answer');
    const initialMessage = document.getElementById('initialMessage');
    const customQueryInput = document.getElementById('customQueryInput');
    const customQueryButton = document.getElementById('customQueryButton');
    
    // Make sure loading is hidden on page load
    loadingIndicator.classList.add('hidden');
    
    // File upload functionality
    uploadButton.addEventListener('click', async function() {
        if (!fileInput.files.length) {
            uploadStatus.textContent = 'Please select a file first';
            return;
        }
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        uploadStatus.textContent = 'Uploading...';
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                uploadStatus.textContent = result.status;
                // Enable prompt buttons after successful upload
                enablePromptButtons();
                // Enable custom query input after successful upload
                enableCustomQuery();
            } else {
                uploadStatus.textContent = `Error: ${result.error || 'Upload failed'}`;
            }
        } catch (error) {
            uploadStatus.textContent = `Error: ${error.message}`;
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
                    // Display answer
                    if (result.answer) {
                        answerContainer.textContent = result.answer;
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
                // Display answer
                if (result.answer) {
                    answerContainer.textContent = result.answer;
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
