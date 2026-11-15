import '@fontsource-variable/dm-sans'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ProvedorDeAvisos } from './componentes/Avisos'
import './estilos.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ProvedorDeAvisos>
        <App />
      </ProvedorDeAvisos>
    </BrowserRouter>
  </React.StrictMode>,
)
