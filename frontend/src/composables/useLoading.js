import { ref } from 'vue'

/**
 * Composable for managing loading states
 * Provides a simple way to track async operations
 */
export function useLoading() {
  const loading = ref(false)
  const error = ref(null)

  /**
   * Execute an async function with loading state management
   * @param {Function} asyncFn - Async function to execute
   * @param {Object} options - Options for error handling
   * @returns {Promise} Result of the async function
   */
  const execute = async (asyncFn, options = {}) => {
    const { 
      showError = true,
      errorMessage = null,
      onError = null 
    } = options

    loading.value = true
    error.value = null

    try {
      const result = await asyncFn()
      return result
    } catch (err) {
      error.value = err

      // Custom error handler
      if (onError) {
        onError(err)
      }

      // Show custom error message if provided
      if (showError && errorMessage) {
        window.dispatchEvent(new CustomEvent('api-error', { 
          detail: { message: errorMessage } 
        }))
      }

      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error state
   */
  const clearError = () => {
    error.value = null
  }

  return {
    loading,
    error,
    execute,
    clearError
  }
}
