import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api'
import { useCompanyStore } from './company'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const loading = ref(false)

  const base = () => `/companies/${useCompanyStore().companyId}`

  async function fetchTasks(projectId = null) {
    loading.value = true
    try {
      const qs = projectId ? `?project_id=${projectId}` : ''
      tasks.value = await api(`${base()}/tasks${qs}`)
    } finally {
      loading.value = false
    }
  }

  // Substitui a tarefa na lista com o retorno do servidor; remove se saiu do escopo atual.
  function replace(task, scopeProjectId) {
    const idx = tasks.value.findIndex((t) => t.id === task.id)
    // No mural geral (scopeProjectId nulo), todas as tarefas (avulsas e de projetos com acesso) permanecem no escopo.
    // No mural de um projeto específico, apenas tarefas daquele projeto permanecem no escopo.
    const inScope = (scopeProjectId === null || scopeProjectId === undefined)
      ? true
      : task.project_id === scopeProjectId
    if (idx === -1) {
      if (inScope) tasks.value.unshift(task)
    } else if (inScope) {
      tasks.value[idx] = task
    } else {
      tasks.value.splice(idx, 1)
    }
    return task
  }

  async function createTask(payload, scopeProjectId = null) {
    const t = await api(`${base()}/tasks`, { method: 'POST', body: payload })
    return replace(t, scopeProjectId)
  }

  async function updateTask(id, patch, scopeProjectId = null) {
    const t = await api(`${base()}/tasks/${id}`, { method: 'PATCH', body: patch })
    return replace(t, scopeProjectId)
  }

  async function claimTask(id, scopeProjectId = null) {
    const t = await api(`${base()}/tasks/${id}/claim`, { method: 'POST' })
    return replace(t, scopeProjectId)
  }

  async function unclaimTask(id, scopeProjectId = null) {
    const t = await api(`${base()}/tasks/${id}/claim`, { method: 'DELETE' })
    return replace(t, scopeProjectId)
  }

  async function setAssignees(id, membershipIds, scopeProjectId = null) {
    const t = await api(`${base()}/tasks/${id}/assignees`, {
      method: 'PUT',
      body: { membership_ids: membershipIds },
    })
    return replace(t, scopeProjectId)
  }

  async function addSubtask(taskId, title, scopeProjectId = null) {
    const t = await api(`${base()}/tasks/${taskId}/subtasks`, { method: 'POST', body: { title } })
    return replace(t, scopeProjectId)
  }

  async function toggleSubtask(taskId, subtaskId, isCompleted, scopeProjectId = null) {
    const t = await api(`${base()}/tasks/${taskId}/subtasks/${subtaskId}`, {
      method: 'PATCH',
      body: { is_completed: isCompleted },
    })
    return replace(t, scopeProjectId)
  }

  async function deleteTask(id) {
    await api(`${base()}/tasks/${id}`, { method: 'DELETE' })
    const idx = tasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) {
      tasks.value.splice(idx, 1)
    }
  }
  // Kanban: grava a ordem final de uma coluna; tarefas de outra coluna mudam de status.
  async function reorderTasks(status, taskIds, projectId = null) {
    taskIds.forEach((id, i) => {
      const t = tasks.value.find((x) => x.id === id)
      if (t) {
        t.status = status
        t.position = i + 1
      }
    })
    try {
      tasks.value = await api(`${base()}/tasks/order`, {
        method: 'PUT',
        body: { status, task_ids: taskIds, project_id: projectId },
      })
    } catch (err) {
      await fetchTasks(projectId).catch(() => {})
      throw err
    }
  }

  return {
    tasks, loading, fetchTasks, createTask, updateTask, claimTask, unclaimTask,
    setAssignees, addSubtask, toggleSubtask, deleteTask, reorderTasks,
  }
})

