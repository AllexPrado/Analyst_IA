import { createApp } from 'vue'
import App from './App.vue'
import './index.css'

import { library } from '@fortawesome/fontawesome-svg-core'
import { 
  faSpinner, faChartBar, faShieldAlt, faChartLine, 
  faWaveSquare, faLightbulb, faComments, faCircle, 
  faExclamationTriangle, faTimesCircle, faRocket,
  faTimes, faRobot, faSun, faMoon, faCheckCircle,
  faChevronRight, faChevronLeft, faExclamationCircle,
  faServer, faDatabase, faMobileAlt, faMicrochip, faCloud,
  faBolt, faNetworkWired, faClock, faDesktop, faTablet,
  faToolbox, faChartPie, faChartArea, faPaperPlane, faCopy,
  faSync, faTrash, faCommentDots, faUser, faEye, faGlobe,
  faHdd, faFilter, faWrench, faPlay, faSearchPlus, faInfo,
  faTachometerAlt, faArrowUp, faArrowDown, faCube, faCubes, faBug,
  faClipboardCheck, faTools, faUserCog, faCodeBranch, faMemory,
  faCloudDownloadAlt, faExternalLinkAlt, faLink,
  faThumbsUp, faThumbsDown, faQuestion, faExchangeAlt, faTrashAlt,
  faBrain, faFileAlt, faProjectDiagram, faInfoCircle
} from '@fortawesome/free-solid-svg-icons'

// Importa todos os ícones de marcas (incluindo kubernetes)
import { fab } from '@fortawesome/free-brands-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

import VueApexCharts from "vue3-apexcharts"
import router from './router.js'
import store from './store.js'
import setupAxiosInterceptors from './interceptors.js'

// Configurar interceptores do Axios
setupAxiosInterceptors()

library.add(
  faSpinner, faChartBar, faShieldAlt, faChartLine, 
  faWaveSquare, faLightbulb, faComments, faCircle, 
  faExclamationTriangle, faTimesCircle, faRocket,
  faTimes, faRobot, faSun, faMoon, faCheckCircle,
  faChevronRight, faChevronLeft, faExclamationCircle,
  faServer, faDatabase, faMobileAlt, faMicrochip, faCloud,
  faBolt, faNetworkWired, faClock, faDesktop, faTablet,
  faToolbox, faChartPie, faChartArea, faPaperPlane, faCopy,
  faSync, faTrash, faCommentDots, faUser, faEye, faGlobe,
  faHdd, faFilter, faWrench, faPlay, faSearchPlus, faInfo,
  faTachometerAlt, faArrowUp, faArrowDown, faCube, faCubes, faBug,
  faClipboardCheck, faTools, faUserCog, faCodeBranch, faMemory,
  faCloudDownloadAlt, faExternalLinkAlt, faLink,
  faThumbsUp, faThumbsDown, faQuestion, faExchangeAlt, faTrashAlt,
  faBrain, faFileAlt, faProjectDiagram, faInfoCircle
)

// Adicionar todos os ícones de marcas
library.add(fab)

const app = createApp(App)
app.use(router)
app.use(store)
app.component('font-awesome-icon', FontAwesomeIcon)
app.component('apexchart', VueApexCharts)
app.mount('#app')