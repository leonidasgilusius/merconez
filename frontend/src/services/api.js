// src/services/api.js

// Document Translation

// Start translation job
export const startDocumentTranslation = async (filePath) => {
  const response = await fetch('/api/v2/translate-document', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_file_path: filePath }),
  })

  if (!response.ok) {
    throw new Error('Failed to start document translation job')
  }

  return response.json()
}

// Check job status (polling)
export const getJobStatus = async (jobId) => {
  const response = await fetch(`/api/v2/job-status/${jobId}`)
  if (!response.ok) {
    throw new Error('Failed to get job status')
  }
  return response.json()
}
