import {useCallback} from 'react';
let csrfToken='';
export function setCsrfToken(value:string){csrfToken=value}
export async function api<T>(path:string,init:RequestInit={}):Promise<T>{
 const method=(init.method||'GET').toUpperCase(); const headers=new Headers(init.headers); headers.set('Accept','application/json');
 if(init.body) headers.set('Content-Type','application/json'); if(!['GET','HEAD','OPTIONS'].includes(method)&&csrfToken)headers.set('X-CSRF-Token',csrfToken);
 const response=await fetch(`/api/v1${path}`,{...init,headers,credentials:'include'}); const payload=await response.json().catch(()=>({}));
 if(!response.ok)throw new Error(payload.message||'Request failed'); if(payload.csrf_token)setCsrfToken(payload.csrf_token); return payload as T;
}
export function useApi(){return useCallback(api,[])}
