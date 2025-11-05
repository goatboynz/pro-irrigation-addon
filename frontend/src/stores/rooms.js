import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useRoomsStore = defineStore('rooms', () => {
  const rooms = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchRooms() {
    loading.value = true
    error.value = null
    try {
      const response = await api.getRooms()
      rooms.value = response.data
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch rooms:', err)
    } finally {
      loading.value = false
    }
  }

  async function getRoom(id) {
    try {
      const response = await api.getRoom(id)
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch room:', err)
      throw err
    }
  }

  async function createRoom(roomData) {
    try {
      const response = await api.createRoom(roomData)
      await fetchRooms()
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Failed to create room:', err)
      throw err
    }
  }

  async function updateRoom(id, roomData) {
    try {
      const response = await api.updateRoom(id, roomData)
      await fetchRooms()
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Failed to update room:', err)
      throw err
    }
  }

  async function deleteRoom(id) {
    try {
      await api.deleteRoom(id)
      await fetchRooms()
    } catch (err) {
      error.value = err.message
      console.error('Failed to delete room:', err)
      throw err
    }
  }

  return {
    rooms,
    loading,
    error,
    fetchRooms,
    getRoom,
    createRoom,
    updateRoom,
    deleteRoom
  }
})
