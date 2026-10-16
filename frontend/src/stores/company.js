import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api'

export const useCompanyStore = defineStore('company', () => {
  const company = ref(null)
  const activeMembership = ref(null)
  const members = ref([])
  const projects = ref([])

  const companyId = computed(() => company.value?.id ?? null)
  const isMasterInCurrentCompany = computed(() => activeMembership.value?.role === 'master')

  async function load(id) {
    const numId = Number(id)
    const data = await api(`/companies/${numId}`)
    company.value = { id: data.id, name: data.name, cnpj: data.cnpj }
    activeMembership.value = data.membership
    try {
      await fetchProjects(data.id)
    } catch (e) {
      console.warn('Aviso: falha ao carregar projetos da empresa:', e)
    }
    try {
      await fetchMembers(data.id)
    } catch (e) {
      console.warn('Aviso: falha ao carregar membros da empresa:', e)
    }
  }

  async function fetchMembers(targetId = companyId.value) {
    const cid = targetId || company.value?.id
    if (!cid) return []
    const res = await api(`/companies/${cid}/members`)
    members.value = res
    return res
  }

  async function fetchProjects(targetId = companyId.value) {
    const cid = targetId || company.value?.id
    if (!cid) return []
    const res = await api(`/companies/${cid}/projects`)
    projects.value = res
    return res
  }

  async function lookupMember(email) {
    return api(`/companies/${companyId.value}/members/lookup?email=${encodeURIComponent(email)}`)
  }

  async function addMember(payload) {
    const res = await api(`/companies/${companyId.value}/members`, { method: 'POST', body: payload })
    await fetchMembers()
    return res
  }

  async function updateMember(membershipId, patch) {
    await api(`/companies/${companyId.value}/members/${membershipId}`, { method: 'PATCH', body: patch })
    await fetchMembers()
  }

  async function createProject(payload) {
    const p = await api(`/companies/${companyId.value}/projects`, { method: 'POST', body: payload })
    await fetchProjects()
    return p
  }

  async function updateProject(id, patch) {
    const p = await api(`/companies/${companyId.value}/projects/${id}`, { method: 'PATCH', body: patch })
    await fetchProjects()
    return p
  }

  async function getVisibility(projectId) {
    return api(`/companies/${companyId.value}/projects/${projectId}/visibility`)
  }

  async function setVisibility(projectId, itemsOrIds) {
    const payload = Array.isArray(itemsOrIds) && itemsOrIds.length > 0 && typeof itemsOrIds[0] === 'object'
      ? { items: itemsOrIds }
      : { membership_ids: itemsOrIds }
    return api(`/companies/${companyId.value}/projects/${projectId}/visibility`, {
      method: 'PUT',
      body: payload,
    })
  }

  async function deleteProject(id) {
    await api(`/companies/${companyId.value}/projects/${id}`, { method: 'DELETE' })
    await fetchProjects()
  }

  function reset() {
    company.value = null
    activeMembership.value = null
    members.value = []
    projects.value = []
  }

  return {
    company, activeMembership, members, projects, companyId, isMasterInCurrentCompany,
    load, fetchMembers, fetchProjects, lookupMember, addMember, updateMember,
    createProject, updateProject, deleteProject, getVisibility, setVisibility, reset,
  }
})
