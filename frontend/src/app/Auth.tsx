import {createContext,useContext,useEffect,useRef,useState,type ReactNode} from 'react';
import {api,setCsrfToken} from '../lib/api';

type User={id:string;username:string;role:string};
type Auth={user:User|null;loading:boolean;login:(username:string,password:string)=>Promise<void>;logout:()=>Promise<void>};
const Ctx=createContext<Auth|null>(null);

export function AuthProvider({children}:{children:ReactNode}){
 const[user,setUser]=useState<User|null>(null);
 const[loading,setLoading]=useState(true);
 const authRevision=useRef(0);
 useEffect(()=>{
  const revision=authRevision.current;
  api<User&{csrf_token:string}>('/auth/me').then(d=>{if(authRevision.current===revision){setUser(d);setCsrfToken(d.csrf_token)}}).catch(()=>{if(authRevision.current===revision)setUser(null)}).finally(()=>{if(authRevision.current===revision)setLoading(false)});
 },[]);
 async function login(username:string,password:string){
  const revision=++authRevision.current;
  try{
   const challenge=await api<{csrf_token:string}>('/auth/csrf');
   setCsrfToken(challenge.csrf_token);
   const d=await api<User&{csrf_token:string}>('/auth/login',{method:'POST',body:JSON.stringify({username,password})});
   if(authRevision.current===revision){setCsrfToken(d.csrf_token);setUser(d)}
  }finally{if(authRevision.current===revision)setLoading(false)}
 }
 async function logout(){
  const revision=++authRevision.current;
  await api('/auth/logout',{method:'POST'});if(authRevision.current===revision){setUser(null);setCsrfToken('')}
 }
 return <Ctx.Provider value={{user,loading,login,logout}}>{children}</Ctx.Provider>;
}
export function useAuth(){const c=useContext(Ctx);if(!c)throw new Error('AuthProvider missing');return c;}
