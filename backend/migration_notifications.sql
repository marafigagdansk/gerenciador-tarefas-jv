-- 1. Evolução da tabela de Projetos (Importância e Prazo)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'em_andamento';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS target_date DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_important BOOLEAN DEFAULT FALSE;

-- 2. Evolução da tabela de Tarefas (Auditoria e Controle de Alerta de Prazo)
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS last_deadline_alert TEXT; -- Valores: 'due_today', 'overdue'

-- 3. Tabela de Notificações (In-App + Controle de Push Local)
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT NOT NULL, -- 'assignment', 'status', 'comment', 'deadline', 'project_risk'
    severity TEXT DEFAULT 'info', -- 'info', 'warning', 'critical'
    is_read BOOLEAN DEFAULT FALSE,
    delivered_browser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, company_id, is_read);
