<script setup>
import { ref, computed } from 'vue'
import { useCompanyStore } from '../stores/company'
import { ROLE_LABELS } from '../api'
import { Plus, X } from 'lucide-vue-next'

const company = useCompanyStore()

const aberto = ref(false)
const email = ref('')
const role = ref('collaborator')
const name = ref('')
const password = ref('')
const lookup = ref(null) // null = e-mail ainda não verificado
const erro = ref('')
const sucesso = ref('')
const carregando = ref(false)

const myMembershipId = computed(() => company.activeMembership?.id ?? null)

function abrir() {
  email.value = ''
  role.value = 'collaborator'
  name.value = ''
  password.value = ''
  lookup.value = null
  erro.value = ''
  aberto.value = true
}

// Passo 1: verificação por e-mail
async function verificar() {
  erro.value = ''
  carregando.value = true
  try {
    lookup.value = await company.lookupMember(email.value)
    if (lookup.value.already_member) erro.value = 'Este usuário já é membro ativo desta empresa.'
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}

function editarEmail() {
  lookup.value = null
  erro.value = ''
}

async function adicionar() {
  erro.value = ''
  carregando.value = true
  try {
    // Cenário B (e-mail existente): senha/nome nunca são enviados.
    const payload = { email: email.value, role: role.value }
    if (!lookup.value.exists) {
      payload.name = name.value
      payload.password = password.value
    }
    const res = await company.addMember(payload)
    sucesso.value = res.user_created
      ? 'Novo usuário criado e vinculado à empresa.'
      : 'Usuário existente vinculado à empresa. Ele usa o mesmo login e senha de sempre.'
    aberto.value = false
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}

async function alterar(m, patch) {
  erro.value = ''
  sucesso.value = ''
  try {
    await company.updateMember(m.id, patch)
  } catch (err) {
    erro.value = err.message
  }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>Colaboradores</h1>
        <p class="subtitle">Gerencie quem tem acesso a esta empresa e com qual papel.</p>
      </div>
      <button id="btn-add-membro" class="btn btn-primary" @click="abrir">
        <Plus :size="16" />
        Adicionar Membro
      </button>
    </div>

    <div v-if="erro && !aberto" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>
    <div v-if="sucesso" class="alert-info" style="margin-bottom: 1rem">{{ sucesso }}</div>

    <table class="members">
      <thead>
        <tr><th>Nome</th><th>E-mail</th><th>Papel</th><th>Situação</th><th>Ações</th></tr>
      </thead>
      <tbody>
        <tr v-for="m in company.members" :key="m.id" :class="{ inactive: !m.is_active }">
          <td>{{ m.name }} <span v-if="m.id === myMembershipId" class="hint">(você)</span></td>
          <td>{{ m.email }}</td>
          <td><span class="badge" :class="`badge-${m.role}`">{{ ROLE_LABELS[m.role] }}</span></td>
          <td>{{ m.is_active ? 'Ativo' : 'Inativo' }}</td>
          <td class="actions">
            <button
              class="btn btn-secondary btn-sm"
              :disabled="!m.is_active"
              @click="alterar(m, { role: m.role === 'master' ? 'collaborator' : 'master' })"
            >
              {{ m.role === 'master' ? 'Tornar Colaborador' : 'Tornar Master' }}
            </button>
            <button
              class="btn btn-sm"
              :class="m.is_active ? 'btn-danger' : 'btn-secondary'"
              @click="alterar(m, { is_active: !m.is_active })"
            >
              {{ m.is_active ? 'Desativar' : 'Reativar' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="aberto" class="modal-backdrop" @click.self="aberto = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>Adicionar Membro à Empresa</h3>
          <button class="btn-icon" @click="aberto = false" aria-label="Fechar">
            <X :size="20" />
          </button>
        </div>
        <form class="modal-body" @submit.prevent="lookup ? adicionar() : verificar()">
          <div v-if="erro" class="alert-error">{{ erro }}</div>

          <div class="form-group">
            <label for="membro-email">E-mail</label>
            <input id="membro-email" v-model="email" type="email" required :disabled="!!lookup" autocomplete="off" />
          </div>
          <div class="form-group">
            <label for="membro-papel">Papel nesta empresa</label>
            <select id="membro-papel" v-model="role">
              <option value="collaborator">Colaborador</option>
              <option value="master">Master</option>
            </select>
          </div>

          <template v-if="lookup && !lookup.exists">
            <p class="alert-info">E-mail novo: informe o nome e uma senha provisória. O usuário deverá criar uma nova senha pessoal no seu primeiro acesso.</p>
            <div class="form-group">
              <label for="membro-nome">Nome completo</label>
              <input id="membro-nome" v-model="name" type="text" required autocomplete="off" />
            </div>
            <div class="form-group">
              <label for="membro-senha">Senha provisória (mín. 6 caracteres)</label>
              <input id="membro-senha" v-model="password" type="password" required minlength="6" autocomplete="new-password" />
            </div>
          </template>
          <p v-else-if="lookup && lookup.exists && !lookup.already_member" class="alert-info">
            <strong>{{ lookup.name }}</strong> já possui cadastro. Será apenas vinculado a esta empresa, mantendo a senha atual.
          </p>

          <div class="modal-footer">
            <button v-if="lookup" type="button" class="btn btn-secondary" @click="editarEmail">Alterar e-mail</button>
            <button type="button" class="btn btn-secondary" @click="aberto = false">Cancelar</button>
            <button
              id="btn-membro-confirmar"
              type="submit"
              class="btn btn-primary"
              :disabled="carregando || (lookup && lookup.already_member)"
            >
              {{ lookup ? 'Adicionar' : 'Verificar e-mail' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<style scoped>
.members {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

th, td {
  text-align: left;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9rem;
}

th {
  color: var(--text-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

tr.inactive td {
  color: var(--text-subtle);
}

.actions {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
</style>
