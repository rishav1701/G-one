import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {api,setCsrfToken} from '../lib/api';

type User={id:string;username:string;role:string};
type Auth={user:User|null;loading:boolean;login:(username:string,password:string)=>Promise<void>;logout:()=>Promise<void>};
const Ctx=createContext<Auth|null>(null);

export function AuthProvider({children}:{children:ReactNode}){
 const[user,setUser]=useState<User|null>(null);
 const[loading,setLoading]=useState(true);
 useEffect(()=>{
  api<User&{csrf_token:string}>('/auth/me').then(d=>{setUser(d);setCsrfToken(d.csrf_token)}).catch(()=>setUser(null)).finally(()=>setLoading(false));
 },[]);
 async function login(username:string,password:string){
  const challenge=await api<{csrf_token:string}>('/auth/csrf');
  setCsrfToken(challenge.csrf_token);
  const d=await api<User&{csrf_token:string}>('/auth/login',{method:'POST',body:JSON.stringify({username,password})});
  setCsrfToken(d.csrf_token);setUser(d);
 }
 async function logout(){
  await api('/auth/logout',{method:'POST'});setUser(null);setCsrfToken('');
 }
 return <Ctx.Provider value={{user,loading,login,logout}}>{children}</Ctx.Provider>;
}
export function useAuth(){const c=useContext(Ctx);if(!c)throw new Error('AuthProvider missing');return c;}
