import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import LimiteDeErro from './components/LimiteDeErro'
import './estilos.css'

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LimiteDeErro area="aplicação">
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </LimiteDeErro>
  </React.StrictMode>,
)
