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
 const demoButton=await screen.findByRole('button',{name:/Continue as clinician/});
 await waitFor(()=>expect(demoButton).toBeEnabled());
 fireEvent.click(demoButton);
 await waitFor(()=>expect(mocks.demoLogin).toHaveBeenCalledWith('clinician'));
});

test('switches the sign-in context without assigning account permissions',()=>{
 mocks.api.mockResolvedValue({enabled:false});
 render(<MemoryRouter><Login/></MemoryRouter>);
 fireEvent.click(screen.getByRole('button',{name:'Administration'}));
 expect(screen.getByRole('button',{name:'Sign in to administration'})).toBeInTheDocument();
 expect(screen.getByText('Access is determined by your account permissions.')).toBeInTheDocument();
});

test('administrator demo tile starts an administrator demo session',async()=>{
 mocks.api.mockResolvedValue({enabled:true});
 render(<MemoryRouter><Login/></MemoryRouter>);
 const adminTile=await screen.findByRole('button',{name:/Continue as administrator/});
 await waitFor(()=>expect(adminTile).toBeEnabled());
 fireEvent.click(adminTile);
 await waitFor(()=>expect(mocks.demoLogin).toHaveBeenCalledWith('admin'));
});

test('account tiles fill the username when local demo sign-in is disabled',async()=>{
 mocks.api.mockResolvedValue({enabled:false});
 render(<MemoryRouter><Login/></MemoryRouter>);
 const adminTile=screen.getByRole('button',{name:/Administrator phaseadmin/});
 await waitFor(()=>expect(adminTile).toBeEnabled());
 fireEvent.click(adminTile);
 expect(screen.getByLabelText('Username')).toHaveValue('phaseadmin');
 expect(screen.getByLabelText('Password')).toHaveValue('');
 expect(screen.getByRole('button',{name:'Sign in to administration'})).toBeInTheDocument();
});
