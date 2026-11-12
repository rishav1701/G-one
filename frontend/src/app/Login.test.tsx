import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {expect,test,vi} from 'vitest';

const mocks=vi.hoisted(()=>({login:vi.fn(),demoLogin:vi.fn(),api:vi.fn()}));
vi.mock('./Auth',()=>({useAuth:()=>({login:mocks.login,demoLogin:mocks.demoLogin})}));
vi.mock('../lib/api',()=>({api:mocks.api}));

import Login from './Login';

test('shows local demo sign-in when the server enables it',async()=>{
 mocks.api.mockResolvedValue({enabled:true});
 render(<MemoryRouter><Login/></MemoryRouter>);
 expect(screen.getByRole('heading',{name:'G One'})).toBeInTheDocument();
 expect(screen.getByRole('group',{name:'Sign-in area'})).toBeInTheDocument();
 expect(screen.getByText('phaseclinician')).toBeInTheDocument();
 expect(screen.getByText(/Administrator accounts cannot enter or change clinical records/)).toBeInTheDocument();
 const demoButton=await screen.findByRole('button',{name:'Continue as clinician'});
 fireEvent.click(demoButton);
 await waitFor(()=>expect(mocks.demoLogin).toHaveBeenCalledOnce());
});

test('switches the sign-in context without assigning account permissions',()=>{
 mocks.api.mockResolvedValue({enabled:false});
 render(<MemoryRouter><Login/></MemoryRouter>);
 fireEvent.click(screen.getByRole('button',{name:'Administration'}));
 expect(screen.getByRole('button',{name:'Sign in to administration'})).toBeInTheDocument();
 expect(screen.getByText('Access is determined by your account permissions.')).toBeInTheDocument();
});
