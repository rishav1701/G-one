import {act,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {beforeEach,expect,test,vi} from 'vitest';

const mocks=vi.hoisted(()=>({api:vi.fn(),setCsrfToken:vi.fn()}));
vi.mock('../lib/api',()=>mocks);

import {AuthProvider,useAuth} from './Auth';

function deferred<T>(){
 let resolve!:(value:T)=>void;
 let reject!:(reason?:unknown)=>void;
 const promise=new Promise<T>((res,rej)=>{resolve=res;reject=rej});
 return {promise,resolve,reject};
}

function AuthProbe(){
 const{login,user,loading}=useAuth();
 return <div>
  <span data-testid="user">{user?.username??'anonymous'}</span>
  <span data-testid="loading">{String(loading)}</span>
  <button onClick={()=>void login('phaseclinician','clinical321')}>Sign in</button>
 </div>;
}

beforeEach(()=>vi.clearAllMocks());

test('a late initial session check cannot clear a successful login',async()=>{
 const oldSessionCheck=deferred<{id:string;username:string;role:string;csrf_token:string}>();
 mocks.api.mockImplementation((path:string)=>{
  if(path==='/auth/me')return oldSessionCheck.promise;
  if(path==='/auth/csrf')return Promise.resolve({csrf_token:'pre-login-token'});
  if(path==='/auth/login')return Promise.resolve({id:'user-1',username:'phaseclinician',role:'SENIOR_CLINICIAN',csrf_token:'session-token'});
  throw new Error(`Unexpected auth request: ${path}`);
 });
 render(<AuthProvider><AuthProbe/></AuthProvider>);
 fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
 await waitFor(()=>expect(screen.getByTestId('user')).toHaveTextContent('phaseclinician'));
 await waitFor(()=>expect(screen.getByTestId('loading')).toHaveTextContent('false'));
 await act(async()=>{oldSessionCheck.reject(new Error('Unauthenticated'));await Promise.resolve()});
 expect(screen.getByTestId('user')).toHaveTextContent('phaseclinician');
 expect(screen.getByTestId('loading')).toHaveTextContent('false');
});
