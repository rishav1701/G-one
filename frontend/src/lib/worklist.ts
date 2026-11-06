import {api} from './api';
import type {Admission,Alert,Assessment,Observation,Page} from './clinical';
export type PatientRow={admission:Admission;assessment?:Assessment;observation?:Observation;previous?:Assessment;alert?:Alert};
export async function loadWorklist():Promise<PatientRow[]>{
 const [admissions,alerts]=await Promise.all([api<Page<Admission>>('/admissions?limit=200&sort=admitted_at&direction=desc'),api<Page<Alert>>('/alerts?limit=200')]);
 return Promise.all(admissions.items.map(async admission=>{
  const [assessments,observations]=await Promise.all([api<Assessment[]>(`/admissions/${admission.id}/assessments?limit=2`),api<Observation[]>(`/admissions/${admission.id}/observations?limit=2`)]);
  const alert=alerts.items.filter(item=>item.admission_id===admission.id&&item.status!=='RESOLVED').sort((a,b)=>new Date(b.created_at).getTime()-new Date(a.created_at).getTime())[0];
  return {admission,assessment:assessments[0],previous:assessments[1],observation:observations[0],alert};
 }));
}
