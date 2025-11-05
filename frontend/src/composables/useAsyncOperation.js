import { ref } from 'vue'

/**
 * Composable for managing async operations with retry logic
 * Provides loading state, error handling, and automatic retries
 */
export function useAsyncOperation() {
  const loading = ref(false)
  const error = ref(null)
  const retrying = ref(false)
  const retryCount = ref(0)

  /**
   * Execute an async operation with retry logic
   * @param {Function} asyncFn - Async function to execute
   * @param {Object} options - Configuration options
   * @returns {Promise} Result of the async function
   */
  const execute = async (asyncFn, options = {}) => {
    const {
      maxRetries = 2,
      retryDelay = 1000,
      shouldRetry = (err) => {
        // Retry on network errors and 5xx server errors
        return !err.response || (err.response.status >= 500 && err.response.status < 600)
      },
      onRetry = null,
      onError = null,
      onSuccess = null
    } = options

    loading.value = true
    error.value = null
    retryCount.value = 0
    retrying.value = false

    const attemptOperation = async (attempt) => {
      try {
        const result = await asyncFn()
        
        // Success callback
        if (onSuccess) {
          onSuccess(result)
        }

        return result
      } catch (err) {
        // Check if we should retry
        if (attempt < maxRetries && shouldRetry(err)) {
          retryCount.value = attempt + 1
          retrying.value = true

          // Retry callback
          if (onRetry) {
            onRetry(retryCount.value, maxRetries)
          }

          // Wait before retrying with exponential backoff
          const delay = retryDelay * Math.pow(2, attempt)
          await new Promise(resolve => setTimeout(resolve, delay))

          // Retry the operation
          return attemptOperation(attempt + 1)
        }

        // Max retries reached or shouldn't retry
        error.value = err

        // Error callback
        if (onError) {
          onError(err)
        }

        throw err
      }
    }

    try {
      return await attemptOperation(0)
    } finally {
      loading.value = false
      retrying.value = false
    }
  }

  /**
   * Clear error state
   */
  const clearError = () => {
    error.value = null
  }

  /**
   * Reset all state
   */
  const reset = () => {
    loading.value = false
    error.value = null
    retrying.value = false
    retryCount.value = 0
  }

  return {
    loading,
    error,
    retrying,
    retryCount,
    execute,
    clearError,
    reset
  }
}
