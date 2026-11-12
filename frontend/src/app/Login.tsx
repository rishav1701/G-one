import {useEffect,useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {Activity,ArrowRight,Eye,EyeOff,LockKeyhole,ShieldCheck,UserRound} from 'lucide-react';
import {useAuth} from './Auth';
import {api} from '../lib/api';

type AccessMode='clinical'|'administration';

export default function Login(){
 const[username,setUsername]=useState('');
 const[password,setPassword]=useState('');
 const[error,setError]=useState('');
 const[credentialNotice,setCredentialNotice]=useState('');
 const[busy,setBusy]=useState(false);
 const[visible,setVisible]=useState(false);
 const[demoAvailable,setDemoAvailable]=useState(false);
 const[demoStatusReady,setDemoStatusReady]=useState(false);
 const[demoAccounts,setDemoAccounts]=useState({clinician:'phaseclinician',admin:'phaseadmin'});
 const[mode,setMode]=useState<AccessMode>('clinical');
 const{login,demoCredentials}=useAuth();
 const navigate=useNavigate();
 useEffect(()=>{
  let mounted=true;
  api<{enabled:boolean;clinician_username?:string;admin_username?:string}>('/auth/demo-status').then(result=>{if(mounted){setDemoAvailable(result.enabled);setDemoAccounts({clinician:result.clinician_username||'phaseclinician',admin:result.admin_username||'phaseadmin'})}}).catch(()=>{if(mounted)setDemoAvailable(false)}).finally(()=>{if(mounted)setDemoStatusReady(true)});
  return()=>{mounted=false};
 },[]);
 async function submit(e:React.FormEvent){
  e.preventDefault();setError('');setCredentialNotice('');setBusy(true);
  try{await login(username,password);navigate('/dashboard',{replace:true})}
  catch(err){setError(err instanceof Error?err.message:'Unable to sign in')}
  finally{setBusy(false)}
 }
 async function useDemoAccount(account:'clinician'|'admin'){
  setMode(account==='admin'?'administration':'clinical');
  setCredentialNotice('');setError('');
  if(!demoAvailable){
   setUsername(account==='admin'?demoAccounts.admin:demoAccounts.clinician);setPassword('');
   window.setTimeout(()=>document.getElementById('password')?.focus(),0);
   return;
  }
  setBusy(true);
  try{
   const credentials=await demoCredentials(account);
   setUsername(credentials.username);setPassword(credentials.password);
   setCredentialNotice(`Demo ${account==='admin'?'administrator':'clinician'} username and password loaded. Select Sign in to continue.`);
   window.setTimeout(()=>document.getElementById('password')?.focus(),0);
  }catch(err){
   setUsername(account==='admin'?demoAccounts.admin:demoAccounts.clinician);setPassword('');
   setError(err instanceof Error?err.message:'Unable to load local demo credentials');
  }finally{setBusy(false)}
 }
 const isClinical=mode==='clinical';
 return <>
  <a className="skip-link" href="#main">Skip to content</a>
  <div className="banner">SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.</div>
  <main id="main" className="login login-page" tabIndex={-1}>
   <header className="login-heading">
    <div className="login-mark" aria-hidden="true"><Activity size={24}/></div>
    <h1>G One</h1>
    <p>Clinical decision support for simulated ward data</p>
   </header>
   <section className="login-panel" aria-label="Sign in to G One">
    <div className="login-mode" role="group" aria-label="Sign-in area">
     <button type="button" aria-pressed={isClinical} className={isClinical?'selected':''} onClick={()=>{setMode('clinical');setError('')}}><Activity size={16} aria-hidden="true"/>Clinical</button>
     <button type="button" aria-pressed={!isClinical} className={!isClinical?'selected':''} onClick={()=>{setMode('administration');setError('')}}><ShieldCheck size={16} aria-hidden="true"/>Administration</button>
    </div>
    <p className="login-mode-note">Access is determined by your account permissions.</p>
    <form onSubmit={submit}>
     <label className="field" htmlFor="username">Username<span className="icon-input"><UserRound size={16} aria-hidden="true"/><input id="username" autoComplete="username" required value={username} onChange={e=>{setUsername(e.target.value);setCredentialNotice('')}}/></span></label>
     <div className="field">
      <label htmlFor="password">Password</label>
      <span className="password-field icon-input">
       <LockKeyhole size={16} aria-hidden="true"/>
       <input id="password" type={visible?'text':'password'} autoComplete="current-password" required value={password} onChange={e=>{setPassword(e.target.value);setCredentialNotice('')}}/>
       <button type="button" className="visibility" aria-label={visible?'Hide password':'Show password'} onClick={()=>setVisible(!visible)}>{visible?<EyeOff aria-hidden="true" size={16}/>:<Eye aria-hidden="true" size={16}/>}</button>
      </span>
     </div>
     {error&&<p className="error" role="alert" aria-live="polite">{error}</p>}
     {credentialNotice&&<p className="login-credential-notice" role="status" aria-live="polite">{credentialNotice}</p>}
     <button className="button login-submit" disabled={busy}>{busy?'Loading demo credentials…':isClinical?'Sign in to clinical workspace':'Sign in to administration'}<ArrowRight size={16} aria-hidden="true"/></button>
    </form>
    <section className="login-demo" aria-labelledby="login-demo-title">
     <h2 id="login-demo-title">Quick demo access</h2>
     <div className="login-access-grid">
      <button type="button" className="login-access-tile quick-access-button" disabled={busy||!demoStatusReady} onClick={()=>{void useDemoAccount('clinician')}}>
       <strong>Demo clinician</strong>
       <span>{demoAccounts.clinician}</span>
       <span className="access-hint">{!demoStatusReady?'Checking local access…':demoAvailable?(busy?'Loading login details…':'Load username and password'): 'Select to fill username; enter the one-time password.'}<ArrowRight size={14} aria-hidden="true"/></span>
      </button>
      <button type="button" className="login-access-tile quick-access-button" disabled={busy||!demoStatusReady} onClick={()=>{void useDemoAccount('admin')}}>
       <strong>Administrator</strong>
       <span>{demoAccounts.admin}</span>
       <span className="access-hint">{!demoStatusReady?'Checking local access…':demoAvailable?(busy?'Loading login details…':'Load username and password'):'Select to fill username; enter the one-time password.'}<ArrowRight size={14} aria-hidden="true"/></span>
      </button>
     </div>
     <p className="demo-footnote">Credential autofill is available only on the localhost development demo. Administrator accounts cannot enter or change clinical records.</p>
    </section>
   </section>
   <footer className="login-footer">G One · simulated ward monitoring demonstration</footer>
  </main>
 </>
}
