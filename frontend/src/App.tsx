import { useState, useEffect, useCallback } from 'react'
import { get, put } from './api'

// ── Types ────────────────────────────────────────────────────────────────────

interface Department { id: number; name: string }
interface Country    { id: number; name: string; currency_code: string }
interface Role       { id: number; title: string; level: string }

interface Employee {
  id: number
  first_name: string
  last_name: string
  email: string
  hire_date: string
  department: Department
  country: Country
  role: Role
  current_salary_amount: number | null
  current_salary_currency: string | null
}

interface SalaryRecord {
  id: number
  amount: string
  currency: string
  effective_date: string
  reason: string | null
  created_at: string
}

interface EmployeeDetail extends Employee {
  salary_history: SalaryRecord[]
}

interface PagedEmployees {
  total: number
  page: number
  page_size: number
  items: Employee[]
}

interface GroupStat {
  name: string
  avg: number | null
  median: number | null
  min: number | null
  max: number | null
  count: number
}

interface OrgSummary {
  total_employees: number
  avg_salary: number | null
  median_salary: number | null
  min_salary: number | null
  max_salary: number | null
  total_payroll: number | null
  headcount_by_department: { name: string; count: number }[]
  headcount_by_country:    { name: string; count: number }[]
  headcount_by_level:      { name: string; count: number }[]
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (n: number | null) =>
  n == null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

const PAGE_SIZE = 50

// ── Sub-components ───────────────────────────────────────────────────────────

function Spinner() {
  return <div className="text-center py-12 text-gray-400">Loading…</div>
}

function ErrorMsg({ msg }: { msg: string }) {
  return <div className="text-red-600 py-4">{msg}</div>
}

// ── Employee List ─────────────────────────────────────────────────────────────

function EmployeeList({ onSelect }: { onSelect: (id: number) => void }) {
  const [data, setData] = useState<PagedEmployees | null>(null)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [deptId, setDeptId] = useState('')
  const [countryId, setCountryId] = useState('')
  const [departments, setDepartments] = useState<Department[]>([])
  const [countries, setCountries] = useState<Country[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    get<Department[]>('/meta/departments').then(setDepartments).catch(() => {})
    get<Country[]>('/meta/countries').then(setCountries).catch(() => {})
  }, [])

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
    if (search)   params.set('search', search)
    if (deptId)   params.set('department_id', deptId)
    if (countryId) params.set('country_id', countryId)
    get<PagedEmployees>(`/employees?${params}`)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [page, search, deptId, countryId])

  useEffect(() => { load() }, [load])

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          className="border rounded px-3 py-1.5 text-sm w-56"
          placeholder="Search name, email, ID…"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
        />
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={deptId}
          onChange={e => { setDeptId(e.target.value); setPage(1) }}
        >
          <option value="">All departments</option>
          {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={countryId}
          onChange={e => { setCountryId(e.target.value); setPage(1) }}
        >
          <option value="">All countries</option>
          {countries.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        {data && (
          <span className="text-sm text-gray-500 self-center">{data.total.toLocaleString()} employees</span>
        )}
      </div>

      {loading && <Spinner />}
      {error && <ErrorMsg msg={error} />}

      {!loading && data && (
        <>
          <div className="overflow-x-auto rounded border">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100 text-left">
                <tr>
                  {['ID', 'Name', 'Department', 'Role', 'Country', 'Current Salary'].map(h => (
                    <th key={h} className="px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map(emp => (
                  <tr
                    key={emp.id}
                    className="border-t hover:bg-blue-50 cursor-pointer"
                    onClick={() => onSelect(emp.id)}
                  >
                    <td className="px-4 py-2 text-gray-400">{emp.id}</td>
                    <td className="px-4 py-2 font-medium">{emp.first_name} {emp.last_name}</td>
                    <td className="px-4 py-2">{emp.department.name}</td>
                    <td className="px-4 py-2">{emp.role.title}</td>
                    <td className="px-4 py-2">{emp.country.name}</td>
                    <td className="px-4 py-2">
                      {emp.current_salary_amount
                        ? `${Number(emp.current_salary_amount).toLocaleString()} ${emp.current_salary_currency}`
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center gap-4 mt-4">
            <button
              className="px-3 py-1 rounded border text-sm disabled:opacity-40"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
            >← Prev</button>
            <span className="text-sm text-gray-600">Page {page} of {totalPages}</span>
            <button
              className="px-3 py-1 rounded border text-sm disabled:opacity-40"
              disabled={page >= totalPages}
              onClick={() => setPage(p => p + 1)}
            >Next →</button>
          </div>
        </>
      )}
    </div>
  )
}

// ── Employee Detail ───────────────────────────────────────────────────────────

function EmployeeDetail({ id, onBack }: { id: number; onBack: () => void }) {
  const [emp, setEmp] = useState<EmployeeDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Salary form
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [effectiveDate, setEffectiveDate] = useState(new Date().toISOString().slice(0, 10))
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  const loadEmp = useCallback(() => {
    setLoading(true)
    get<EmployeeDetail>(`/employees/${id}`)
      .then(e => {
        setEmp(e)
        setLoading(false)
        // Default currency to the employee's own currency
        setCurrency(e.country.currency_code)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [id])

  useEffect(() => { loadEmp() }, [loadEmp])

  const handleSalaryUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setSaveMsg('')
    try {
      await put(`/employees/${id}/salary`, {
        amount: parseFloat(amount),
        currency,
        effective_date: effectiveDate,
        reason: reason || null,
      })
      setSaveMsg('✓ Salary updated')
      setAmount('')
      setReason('')
      loadEmp()
    } catch (err: any) {
      setSaveMsg(`Error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Spinner />
  if (error) return <ErrorMsg msg={error} />
  if (!emp) return null

  return (
    <div>
      <button onClick={onBack} className="text-blue-600 text-sm mb-4 hover:underline">← Back to list</button>

      {/* Employee info */}
      <div className="bg-white border rounded p-4 mb-6">
        <h2 className="text-xl font-semibold mb-1">{emp.first_name} {emp.last_name}</h2>
        <p className="text-gray-500 text-sm mb-3">{emp.email}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div><span className="text-gray-500">Department</span><br />{emp.department.name}</div>
          <div><span className="text-gray-500">Role</span><br />{emp.role.title} ({emp.role.level})</div>
          <div><span className="text-gray-500">Country</span><br />{emp.country.name}</div>
          <div><span className="text-gray-500">Hire Date</span><br />{emp.hire_date}</div>
        </div>
        {emp.current_salary_amount && (
          <div className="mt-3 text-lg font-medium">
            Current salary: {Number(emp.current_salary_amount).toLocaleString()} {emp.current_salary_currency}
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Update salary form */}
        <div className="bg-white border rounded p-4">
          <h3 className="font-medium mb-3">Update Salary</h3>
          <form onSubmit={handleSalaryUpdate} className="space-y-3">
            <div>
              <label className="text-sm text-gray-600">Amount</label>
              <input
                required type="number" min="0" step="0.01"
                className="w-full border rounded px-3 py-1.5 text-sm mt-1"
                value={amount}
                onChange={e => setAmount(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-gray-600">Currency</label>
              <input
                className="w-full border rounded px-3 py-1.5 text-sm mt-1"
                value={currency}
                onChange={e => setCurrency(e.target.value)}
                maxLength={3}
              />
            </div>
            <div>
              <label className="text-sm text-gray-600">Effective Date</label>
              <input
                required type="date"
                className="w-full border rounded px-3 py-1.5 text-sm mt-1"
                value={effectiveDate}
                onChange={e => setEffectiveDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-gray-600">Reason (optional)</label>
              <input
                className="w-full border rounded px-3 py-1.5 text-sm mt-1"
                value={reason}
                onChange={e => setReason(e.target.value)}
                placeholder="e.g. Annual review"
              />
            </div>
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
            {saveMsg && <p className="text-sm mt-1 text-green-600">{saveMsg}</p>}
          </form>
        </div>

        {/* Salary history */}
        <div className="bg-white border rounded p-4">
          <h3 className="font-medium mb-3">Salary History</h3>
          {emp.salary_history.length === 0 ? (
            <p className="text-gray-400 text-sm">No records yet.</p>
          ) : (
            <div className="space-y-2">
              {[...emp.salary_history].reverse().map(r => (
                <div key={r.id} className="border-b pb-2 text-sm">
                  <span className="font-medium">{Number(r.amount).toLocaleString()} {r.currency}</span>
                  <span className="text-gray-400 ml-2">{r.effective_date}</span>
                  {r.reason && <span className="text-gray-500 ml-2">— {r.reason}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Analytics ─────────────────────────────────────────────────────────────────

function Analytics() {
  const [summary, setSummary] = useState<OrgSummary | null>(null)
  const [byDept, setByDept] = useState<GroupStat[]>([])
  const [byCountry, setByCountry] = useState<GroupStat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      get<OrgSummary>('/analytics/summary'),
      get<GroupStat[]>('/analytics/by-department'),
      get<GroupStat[]>('/analytics/by-country'),
    ])
      .then(([s, d, c]) => { setSummary(s); setByDept(d); setByCountry(c) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorMsg msg={error} />
  if (!summary) return null

  return (
    <div className="space-y-6">
      {/* Org-wide stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Employees', value: summary.total_employees.toLocaleString() },
          { label: 'Avg Salary',      value: fmt(summary.avg_salary) },
          { label: 'Median Salary',   value: fmt(summary.median_salary) },
          { label: 'Total Payroll',   value: fmt(summary.total_payroll) },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border rounded p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
            <div className="text-2xl font-semibold mt-1">{value}</div>
          </div>
        ))}
      </div>

      {/* By Department */}
      <div className="bg-white border rounded p-4">
        <h3 className="font-medium mb-3">Salary by Department</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-gray-500 border-b">
              <tr>
                {['Department', 'Headcount', 'Avg', 'Median', 'Min', 'Max'].map(h => (
                  <th key={h} className="pb-2 pr-6">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {byDept.map(r => (
                <tr key={r.name} className="border-b last:border-0">
                  <td className="py-1.5 pr-6 font-medium">{r.name}</td>
                  <td className="py-1.5 pr-6">{r.count}</td>
                  <td className="py-1.5 pr-6">{fmt(r.avg)}</td>
                  <td className="py-1.5 pr-6">{fmt(r.median)}</td>
                  <td className="py-1.5 pr-6">{fmt(r.min)}</td>
                  <td className="py-1.5 pr-6">{fmt(r.max)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* By Country */}
      <div className="bg-white border rounded p-4">
        <h3 className="font-medium mb-3">Salary by Country</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-gray-500 border-b">
              <tr>
                {['Country', 'Headcount', 'Avg', 'Median'].map(h => (
                  <th key={h} className="pb-2 pr-6">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {byCountry.map(r => (
                <tr key={r.name} className="border-b last:border-0">
                  <td className="py-1.5 pr-6 font-medium">{r.name}</td>
                  <td className="py-1.5 pr-6">{r.count}</td>
                  <td className="py-1.5 pr-6">{fmt(r.avg)}</td>
                  <td className="py-1.5 pr-6">{fmt(r.median)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Headcount by Level */}
      <div className="bg-white border rounded p-4">
        <h3 className="font-medium mb-3">Headcount by Level</h3>
        <div className="flex flex-wrap gap-3">
          {summary.headcount_by_level.map(l => (
            <div key={l.name} className="border rounded px-3 py-2 text-sm">
              <span className="font-medium capitalize">{l.name}</span>
              <span className="text-gray-500 ml-2">{l.count.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────

type Tab = 'employees' | 'analytics'

export default function App() {
  const [tab, setTab] = useState<Tab>('employees')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [listKey, setListKey] = useState(0)

  const handleBack = () => {
    setSelectedId(null)
    setListKey(k => k + 1)   // force EmployeeList to remount + re-fetch
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-3 flex items-center gap-6">
        <h1 className="font-semibold text-gray-800">ACME Salary Manager</h1>
        <nav className="flex gap-1">
          {(['employees', 'analytics'] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => { setTab(t); setSelectedId(null) }}
              className={`px-3 py-1.5 rounded text-sm capitalize ${
                tab === t ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {tab === 'employees' && (
          selectedId
            ? <EmployeeDetail id={selectedId} onBack={handleBack} />
            : <EmployeeList key={listKey} onSelect={setSelectedId} />
        )}
        {tab === 'analytics' && <Analytics />}
      </main>
    </div>
  )
}
