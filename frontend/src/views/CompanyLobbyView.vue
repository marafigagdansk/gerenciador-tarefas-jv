<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import CardEmpresa from '../components/CardEmpresa.vue'
import ModalEmpresa from '../components/ModalEmpresa.vue'

const auth = useAuthStore()
const router = useRouter()
const modalAberto = ref(false)

function abrir(m) {
  router.push({ name: 'tasks', params: { companyId: m.company_id } })
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
        + Nova Empresa
      </button>
    </div>

    <div v-if="auth.memberships.length === 0" class="empty-box">
      <h3>Nenhuma empresa vinculada</h3>
      <p>Peça a um Master para adicionar você a uma empresa.</p>
    </div>

    <div v-else class="empresas-grid">
      <CardEmpresa v-for="m in auth.memberships" :key="m.membership_id" :membership="m" @select="abrir" />
    </div>

    <ModalEmpresa :is-open="modalAberto" @close="modalAberto = false" />
  </main>
</template>

<style scoped>
.empresas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}
</style>
