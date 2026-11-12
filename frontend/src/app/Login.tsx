import {useEffect,useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {Eye,EyeOff} from 'lucide-react';
import {useAuth} from './Auth';
import {api} from '../lib/api';

export default function Login(){
 const[username,setUsername]=useState('');
 const[password,setPassword]=useState('');
 const[error,setError]=useState('');
 const[busy,setBusy]=useState(false);
 const[visible,setVisible]=useState(false);
 const[demoAvailable,setDemoAvailable]=useState(false);
 const{login,demoLogin}=useAuth();
 const navigate=useNavigate();
 useEffect(()=>{
  let mounted=true;
  api<{enabled:boolean}>('/auth/demo-status').then(result=>{if(mounted)setDemoAvailable(result.enabled)}).catch(()=>{if(mounted)setDemoAvailable(false)});
  return()=>{mounted=false};
 },[]);
 async function submit(e:React.FormEvent){
  e.preventDefault();setError('');setBusy(true);
  try{await login(username,password);navigate('/dashboard',{replace:true})}
  catch(err){setError(err instanceof Error?err.message:'Unable to sign in')}
  finally{setBusy(false)}
 }
 async function submitDemo(){
  setError('');setBusy(true);
  try{await demoLogin();navigate('/dashboard',{replace:true})}
  catch(err){setError(err instanceof Error?err.message:'Demo sign-in is unavailable')}
  finally{setBusy(false)}
 }
 return <>
  <a className="skip-link" href="#main">Skip to content</a>
  <div className="banner">SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.</div>
  <main id="main" className="login" tabIndex={-1}>
   <h1>G One</h1>
   <p>Clinical decision-support demonstration for simulated ward data.</p>
   <form onSubmit={submit}>
    <label className="field" htmlFor="username">Username<input id="username" autoComplete="username" required value={username} onChange={e=>setUsername(e.target.value)}/></label>
    <div className="field">
     <label htmlFor="password">Password</label>
     <span className="password-field">
      <input id="password" type={visible?'text':'password'} autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)}/>
      <button type="button" className="visibility" aria-label={visible?'Hide password':'Show password'} onClick={()=>setVisible(!visible)}>{visible?<EyeOff aria-hidden="true" size={16}/>:<Eye aria-hidden="true" size={16}/>}</button>
     </span>
    </div>
    {error&&<p className="error" role="alert" aria-live="polite">{error}</p>}
    <button className="button" disabled={busy}>{busy?'Signing in…':'Sign in'}</button>
   </form>
   <section className="login-demo" aria-labelledby="login-demo-title">
    <h2 id="login-demo-title">Demo access for judges</h2>
    <p>For patient records, manual observations, and alert actions, sign in as <strong>SENIOR_CLINICIAN</strong>. The default username is <code>phaseclinician</code>.</p>
    <p>Start <code>scripts/demo.ps1</code> from the project folder. ADMIN is for demonstration controls and cannot enter clinical data.</p>
    {demoAvailable&&<div className="demo-signin"><button type="button" className="button" disabled={busy} onClick={submitDemo}>{busy?'Starting demo session…':'Continue as demo clinician'}</button><p className="muted">Local demonstration sign-in. It starts a normal session and does not display the account password.</p></div>}
   </section>
  </main>
 </>
}
