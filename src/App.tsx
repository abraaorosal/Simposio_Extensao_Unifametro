import { useMemo, useState } from 'react'
import data from './data/presentations.json'
import './App.css'

type PresentationStatus = 'complete' | 'missing_schedule' | 'missing_poster'

type Presentation = {
  id: string
  title: string
  course: string
  discipline: string
  campus: string
  availability: string
  period: 'MANHÃ' | 'NOITE' | 'PENDENTE'
  posterUrl: string
  notes: string
  leadEmail: string
  members: string[]
  memberCount: number
  status: PresentationStatus
}

type PresentationData = {
  generatedAt: string
  totals: {
    posterSubmissions: number
    scheduleChoices: number
    records: number
    complete: number
    missingSchedule: number
    missingPoster: number
  }
  availabilityOptions: string[]
  records: Presentation[]
}

const source = data as PresentationData
const presentations = source.records
const logoPath = `${import.meta.env.BASE_URL}unifametro.png`

const statusMeta: Record<
  PresentationStatus,
  { label: string; tone: string; helper: string }
> = {
  complete: {
    label: 'Completo',
    tone: 'success',
    helper: 'Horário definido e e-pôster vinculado.',
  },
  missing_schedule: {
    label: 'Sem horário',
    tone: 'warning',
    helper: 'Envio encontrado, mas sem escolha de data/horário.',
  },
  missing_poster: {
    label: 'Sem pôster',
    tone: 'danger',
    helper: 'Horário escolhido sem correspondência confiável no envio.',
  },
}

const periodLabel: Record<Presentation['period'], string> = {
  MANHÃ: 'Manhã',
  NOITE: 'Noite',
  PENDENTE: 'Pendente',
}

const availabilityLabel = (value: string) =>
  value === 'PENDENTE' ? 'Pendências' : value

function App() {
  const availabilityTabs = useMemo(
    () => ['TODOS', ...source.availabilityOptions] as const,
    []
  )
  const [selectedAvailability, setSelectedAvailability] = useState<
    (typeof availabilityTabs)[number]
  >('TODOS')
  const [selectedStatus, setSelectedStatus] = useState<
    PresentationStatus | 'TODOS'
  >('TODOS')
  const [disciplineFilter, setDisciplineFilter] = useState('todas')
  const [search, setSearch] = useState('')

  const disciplines = useMemo(
    () =>
      Array.from(new Set(presentations.map((item) => item.discipline)))
        .filter(Boolean)
        .sort((left, right) => left.localeCompare(right)),
    []
  )

  const filteredPresentations = useMemo(() => {
    const query = search.trim().toLowerCase()

    return presentations
      .filter((item) =>
        selectedAvailability === 'TODOS'
          ? true
          : item.availability === selectedAvailability
      )
      .filter((item) =>
        selectedStatus === 'TODOS' ? true : item.status === selectedStatus
      )
      .filter((item) =>
        disciplineFilter === 'todas'
          ? true
          : item.discipline.toLowerCase() === disciplineFilter
      )
      .filter((item) => {
        if (!query) return true

        const haystack = [
          item.title,
          item.course,
          item.discipline,
          item.campus,
          item.leadEmail,
          item.members.join(' '),
        ]
          .join(' ')
          .toLowerCase()

        return haystack.includes(query)
      })
      .sort((left, right) => left.title.localeCompare(right.title))
  }, [disciplineFilter, search, selectedAvailability, selectedStatus])

  const groupedByDiscipline = useMemo(() => {
    return filteredPresentations.reduce<Record<string, Presentation[]>>(
      (groups, item) => {
        const key = item.discipline || 'Sem disciplina informada'
        if (!groups[key]) groups[key] = []
        groups[key].push(item)
        return groups
      },
      {}
    )
  }, [filteredPresentations])

  const filteredCounts = useMemo(
    () => ({
      total: filteredPresentations.length,
      complete: filteredPresentations.filter((item) => item.status === 'complete')
        .length,
      withPoster: filteredPresentations.filter((item) => item.posterUrl).length,
      pending: filteredPresentations.filter((item) => item.status !== 'complete')
        .length,
    }),
    [filteredPresentations]
  )

  return (
    <div className="app-shell">
      <div className="backdrop" aria-hidden />

      <header className="hero">
        <div className="brand">
          <img
            src={logoPath}
            alt="Logo Unifametro"
            className="brand__logo"
          />
          <div>
            <p className="eyebrow">III Simpósio de Extensão Curricular</p>
            <h1>Apresentações de E-pôster</h1>
            <p className="lead">
              Consulta consolidada a partir das respostas de envio do pôster e
              escolha de data/horário. Pesquise por título, disciplina ou nome
              de integrante para localizar sua equipe.
            </p>
            <div className="hero__tags">
              <span className="tag">Projetos: {source.totals.records}</span>
              <span className="tag">Completos: {source.totals.complete}</span>
              <span className="tag">Sem horário: {source.totals.missingSchedule}</span>
              <span className="tag emphasis">
                Atualizado em {source.generatedAt}
              </span>
            </div>
          </div>
        </div>
      </header>

      <section className="panel">
        <div className="filters">
          <div className="day-tabs" aria-label="Selecione o lote de apresentação">
            {availabilityTabs.map((availability) => (
              <button
                key={availability}
                className={`tab ${
                  availability === selectedAvailability ? 'is-active' : ''
                }`}
                onClick={() => setSelectedAvailability(availability)}
              >
                {availability === 'TODOS'
                  ? 'Todas as equipes'
                  : availabilityLabel(availability)}
              </button>
            ))}
          </div>

          <div className="filter-row">
            <div className="chip-group" aria-label="Filtrar por status">
              {[
                ['TODOS', 'Todos'],
                ['complete', 'Completos'],
                ['missing_schedule', 'Sem horário'],
                ['missing_poster', 'Sem pôster'],
              ].map(([value, label]) => (
                <button
                  key={value}
                  className={`chip ${
                    selectedStatus === value ? 'chip--active' : ''
                  }`}
                  onClick={() =>
                    setSelectedStatus(value as PresentationStatus | 'TODOS')
                  }
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="filter-inputs">
              <label className="field">
                <span>Disciplina</span>
                <select
                  value={disciplineFilter}
                  onChange={(event) =>
                    setDisciplineFilter(event.target.value.toLowerCase())
                  }
                >
                  <option value="todas">Todas</option>
                  {disciplines.map((discipline) => (
                    <option key={discipline} value={discipline.toLowerCase()}>
                      {discipline}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field grow">
                <span>Busca geral</span>
                <input
                  type="search"
                  placeholder="Título, integrante, curso ou e-mail"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
            </div>
          </div>
        </div>

        <div className="stats">
          <div className="stat-card">
            <p className="stat-label">Projetos filtrados</p>
            <p className="stat-value">{filteredCounts.total}</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Registros completos</p>
            <p className="stat-value">{filteredCounts.complete}</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Com link do pôster</p>
            <p className="stat-value">{filteredCounts.withPoster}</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Pendências</p>
            <p className="stat-value">{filteredCounts.pending}</p>
          </div>
        </div>

        <div className="summary-banner">
          <p>
            <strong>Envios de E-pôster:</strong> {source.totals.posterSubmissions}
          </p>
          <p>
            <strong>Escolhas de horário:</strong> {source.totals.scheduleChoices}
          </p>
          <p>
            <strong>Pendências detectadas:</strong>{' '}
            {source.totals.missingSchedule + source.totals.missingPoster}
          </p>
        </div>

        <div className="grid">
          {Object.keys(groupedByDiscipline).length === 0 && (
            <div className="empty">Nada encontrado com estes filtros.</div>
          )}

          {Object.entries(groupedByDiscipline)
            .sort(([left], [right]) => left.localeCompare(right))
            .map(([discipline, items]) => (
              <article key={discipline} className="room-card">
                <header className="room-card__header room-card__header--stacked">
                  <div>
                    <p className="eyebrow">Disciplina</p>
                    <h3>{discipline}</h3>
                    <p className="room-card__day">{items.length} equipe(s)</p>
                  </div>
                  <span className="badge">{items[0]?.course || 'Curso não informado'}</span>
                </header>

                <ul className="session-list">
                  {items.map((item) => {
                    const meta = statusMeta[item.status]

                    return (
                      <li key={item.id} className="session session--detailed">
                        <div className="session__topline">
                          <span className={`pill pill--${item.period.toLowerCase()}`}>
                            {periodLabel[item.period]}
                          </span>
                          <span className={`status-badge status-badge--${meta.tone}`}>
                            {meta.label}
                          </span>
                        </div>

                        <p className="session__title">{item.title}</p>
                        <p className="session__subtitle">{item.availability}</p>
                        <p className="session__helper">{meta.helper}</p>

                        <div className="session__meta">
                          <span>{item.memberCount} integrante(s)</span>
                          {item.campus && <span>{item.campus}</span>}
                        </div>

                        {item.members.length > 0 && (
                          <div className="member-list">
                            {item.members.map((member) => (
                              <span key={`${item.id}-${member}`} className="member-chip">
                                {member}
                              </span>
                            ))}
                          </div>
                        )}

                        <div className="session__actions">
                          {item.posterUrl ? (
                            <a
                              className="session-link"
                              href={item.posterUrl}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Abrir e-pôster
                            </a>
                          ) : (
                            <span className="session-link session-link--muted">
                              Link do pôster não localizado
                            </span>
                          )}

                          {item.leadEmail && (
                            <a className="session-email" href={`mailto:${item.leadEmail}`}>
                              {item.leadEmail}
                            </a>
                          )}
                        </div>

                        {item.notes && <p className="session__notes">Obs.: {item.notes}</p>}
                      </li>
                    )
                  })}
                </ul>
              </article>
            ))}
        </div>
      </section>
    </div>
  )
}

export default App
