<script setup>
import { ref, onMounted } from 'vue'
import ModalEmpresa from './components/ModalEmpresa.vue'
import CardEmpresa from './components/CardEmpresa.vue'
import WorkspaceEmpresa from './components/WorkspaceEmpresa.vue'

const empresas = ref([])
const carregando = ref(true)
const modalAberto = ref(false)
const empresaSelecionada = ref(null)

async function buscarEmpresas() {
  carregando.value = true
  try {
    const res = await fetch('/api/empresas')
    if (res.ok) {
      empresas.value = await res.json()
      // Se não houver nenhuma empresa cadastrada inicialmente, abre o modal automaticamente
      if (empresas.value.length === 0) {
        modalAberto.value = true
      }
    }
  } catch (err) {
    console.error('Erro ao buscar empresas:', err)
  } finally {
    carregando.value = false
  }
}

function aoCriarEmpresa(novaEmpresa) {
  empresas.value.unshift(novaEmpresa)
}

async function deletarEmpresa(id) {
  if (!confirm('Deseja realmente remover esta empresa?')) return
  try {
    const res = await fetch(`/api/empresas/${id}`, { method: 'DELETE' })
    if (res.ok) {
      empresas.value = empresas.value.filter(e => e.id !== id)
      if (empresaSelecionada.value?.id === id) {
        empresaSelecionada.value = null
      }
    }
  } catch (err) {
    console.error('Erro ao deletar empresa:', err)
  }
}

function selecionarEmpresa(empresa) {
  empresaSelecionada.value = empresa
}

function voltarInicio() {
  empresaSelecionada.value = null
}

onMounted(() => {
  buscarEmpresas()
})
</script>

<template>
  <div class="app-root">
    <!-- Navbar simples e leve -->
    <header class="navbar">
      <div class="navbar-container">
        <div class="brand" @click="voltarInicio">
          <div class="brand-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10H7v-2h10v2zm-4 4H7v-2h6v2zm4-8H7V7h10v2z"/>
            </svg>
          </div>
          <span class="brand-title">Gerenciador de Tarefas</span>
        </div>

        <div v-if="!empresaSelecionada" class="nav-actions">
          <button class="btn btn-primary" @click="modalAberto = true">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Nova Empresa
          </button>
        </div>
      </div>
    </header>

    <!-- Conteúdo Principal -->
    <div class="container">
      <!-- Se uma empresa estiver aberta -->
      <WorkspaceEmpresa
        v-if="empresaSelecionada"
        :empresa="empresaSelecionada"
        @back="voltarInicio"
      />

      <!-- Tela Inicial de Empresas -->
      <main v-else class="home-view">
        <div class="section-header">
          <div>
            <h1>Empresas</h1>
            <p class="subtitle">Selecione uma empresa para gerenciar ou cadastre uma nova.</p>
          </div>
        </div>

        <!-- Carregando -->
        <div v-if="carregando" class="loading-state">
          <div class="spinner"></div>
          <span>Carregando empresas...</span>
        </div>

        <!-- Lista Vazia -->
        <div v-else-if="empresas.length === 0" class="empty-list-card">
          <div class="empty-icon-box">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
              <path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/>
            </svg>
          </div>
          <h3>Nenhuma empresa cadastrada</h3>
          <p>Para começar a organizar suas tarefas, cadastre sua primeira empresa.</p>
          <button class="btn btn-primary" @click="modalAberto = true">
            Cadastrar Empresa
          </button>
        </div>

        <!-- Grid de Cards de Empresas -->
        <div v-else class="empresas-grid">
          <CardEmpresa
            v-for="emp in empresas"
            :key="emp.id"
            :empresa="emp"
            @select="selecionarEmpresa"
            @delete="deletarEmpresa"
          />
        </div>
      </main>
    </div>

    <!-- Modal de Cadastro -->
    <ModalEmpresa
      :is-open="modalAberto"
      @close="modalAberto = false"
      @created="aoCriarEmpresa"
    />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  border-bottom: 1px solid var(--border-color);
  background: rgba(11, 15, 25, 0.8);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 40;
}

.navbar-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.9rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.brand-icon {
  width: 32px;
  height: 32px;
  background: var(--primary);
  color: #fff;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-title {
  font-weight: 700;
  font-size: 1.1rem;
  letter-spacing: -0.01em;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.75rem;
}

.section-header h1 {
  font-size: 1.6rem;
  font-weight: 700;
  color: #fff;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.empresas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem 0;
  color: var(--text-muted);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-list-card {
  text-align: center;
  padding: 3.5rem 1.5rem;
  background: var(--bg-card);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-lg);
  max-width: 480px;
  margin: 2rem auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.empty-icon-box {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-subtle);
}

.empty-list-card h3 {
  font-size: 1.25rem;
  color: #fff;
}

.empty-list-card p {
  color: var(--text-muted);
  font-size: 0.9rem;
  max-width: 320px;
  line-height: 1.4;
}
</style>
