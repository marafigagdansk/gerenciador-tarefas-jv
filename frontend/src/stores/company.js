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
      await Promise.all([fetchMembers(data.id), fetchProjects(data.id)])
    } catch (e) {
      console.warn('Aviso: falha ao carregar membros ou projetos secundários:', e)
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
    const r = await api(`/companies/${companyId.value}/projects/${projectId}/visibility`)
    return r.membership_ids
  }

  async function setVisibility(projectId, ids) {
    await api(`/companies/${companyId.value}/projects/${projectId}/visibility`, {
      method: 'PUT',
      body: { membership_ids: ids },
    })
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
    createProject, updateProject, getVisibility, setVisibility, reset,
  }
})
