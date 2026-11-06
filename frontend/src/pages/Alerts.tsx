import {Link} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {ApiError,api} from '../lib/api';
import type {Alert,Page} from '../lib/clinical';
import {fmtTime,relative} from '../lib/clinical';
import {LevelBadge} from '../components/LevelBadge';
import {StateBlock} from '../components/StateBlock';

export default function Alerts(){
 const q=useQuery({queryKey:['alerts-page'],queryFn:()=>api<Page<Alert>>('/alerts?limit=200'),refetchInterval:10000});
 if(q.isLoading)return <main className="page"><h1>Alerts</h1><div className="skeleton"/></main>;
 if(q.isError)return <main className="page"><h1>Alerts</h1>{q.error instanceof ApiError&&q.error.status===404?<StateBlock state="forbidden">Alert list not found for this account.</StateBlock>:<StateBlock state="error"><span>Unable to load alerts. Request ID: {q.error instanceof ApiError?q.error.requestId:'Unavailable'}.</span> <button className="quiet" onClick={()=>void q.refetch()}>Retry</button></StateBlock>}</main>;
 const items=(q.data?.items||[]).filter(a=>a.status!=='RESOLVED').sort((a,b)=>Number(b.level==='HIGH')-Number(a.level==='HIGH')||new Date(a.created_at).getTime()-new Date(b.created_at).getTime());
 return <main className="page"><div className="page-heading"><div><h1>Alerts</h1><p>Open alerts from the demonstration worklist.</p></div><span className="muted">Last updated {fmtTime(new Date(q.dataUpdatedAt).toISOString())}</span></div><section className="panel">{!items.length?<StateBlock state="empty">No open alerts are recorded.</StateBlock>:<div className="table-scroll"><table className="clinical-table"><thead><tr><th>Level</th><th>Patient</th><th>Ward / bed</th><th>Status</th><th>Alert age</th><th>Score state</th></tr></thead><tbody>{items.map(a=><tr key={a.id}><td><LevelBadge level={a.level}/></td><td><Link to={`/patients/${a.patient_id}?tab=timeline`}>{a.patient_identifier}</Link></td><td>{a.ward_name} · {a.bed_label}</td><td>{a.status}</td><td title={fmtTime(a.created_at)}>{relative(a.created_at)}</td><td>{a.score_returned_to_low?'Score returned to low':'Current score remains active'}</td></tr>)}</tbody></table></div>}</section></main>;
}
