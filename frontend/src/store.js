import { createStore } from 'vuex'

export default createStore({
  state: {
    darkMode: true,
  },
  mutations: {
    toggleDarkMode(state) {
      state.darkMode = !state.darkMode
      if (state.darkMode) {
        document.body.classList.add('dark')
      } else {
        document.body.classList.remove('dark')
      }
    },
    setDarkMode(state, value) {
      state.darkMode = value
      if (value) {
        document.body.classList.add('dark')
      } else {
        document.body.classList.remove('dark')
      }
    }
  },
})
