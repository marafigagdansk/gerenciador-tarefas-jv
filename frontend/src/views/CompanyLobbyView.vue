<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { Plus } from 'lucide-vue-next'
import CardEmpresa from '../components/CardEmpresa.vue'
import ModalEmpresa from '../components/ModalEmpresa.vue'
import ModalEditarEmpresa from '../components/ModalEditarEmpresa.vue'
import ModalExcluirEmpresa from '../components/ModalExcluirEmpresa.vue'

const auth = useAuthStore()
const modalAberto = ref(false)

const empresaParaEditar = ref(null)
const modalEditarAberto = ref(false)

const empresaParaExcluir = ref(null)
const modalExcluirAberto = ref(false)

function onEditar(membership) {
  empresaParaEditar.value = membership
  modalEditarAberto.value = true
}

function onExcluir(membership) {
  empresaParaExcluir.value = membership
  modalExcluirAberto.value = true
}
</script>

<template>
  <main class="container">
    <div class="page-header">
      <div>
        <h1>Suas empresas</h1>
        <p class="subtitle">Selecione uma empresa para abrir o workspace.</p>
      </div>
      <button v-if="auth.canCreateCompany" id="btn-nova-empresa" class="btn btn-primary" @click="modalAberto = true">
        <Plus :size="16" />
        Nova Empresa
      </button>
    </div>

    <div v-if="auth.memberships.length === 0" class="empty-box">
      <h3>Nenhuma empresa vinculada</h3>
      <p>Peça a um Master para adicionar você a uma empresa.</p>
    </div>

    <div v-else class="empresas-grid">
      <CardEmpresa
        v-for="m in auth.memberships"
        :key="m.membership_id"
        :membership="m"
        @editar="onEditar"
        @excluir="onExcluir"
      />
    </div>

    <ModalEmpresa :is-open="modalAberto" @close="modalAberto = false" />
    <ModalEditarEmpresa
      :is-open="modalEditarAberto"
      :empresa="empresaParaEditar"
      @close="modalEditarAberto = false"
      @saved="modalEditarAberto = false"
    />
    <ModalExcluirEmpresa
      :is-open="modalExcluirAberto"
      :empresa="empresaParaExcluir"
      @close="modalExcluirAberto = false"
      @deleted="modalExcluirAberto = false"
    />
  </main>
</template>

<style scoped>
.empresas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}
</style>
