import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {beforeEach,expect,test,vi} from 'vitest';

const mocks=vi.hoisted(()=>({login:vi.fn(),demoCredentials:vi.fn(),api:vi.fn()}));
vi.mock('./Auth',()=>({useAuth:()=>({login:mocks.login,demoCredentials:mocks.demoCredentials})}));
vi.mock('../lib/api',()=>({api:mocks.api}));

import Login from './Login';

beforeEach(()=>vi.clearAllMocks());

test('loads local demo credentials into the sign-in fields',async()=>{
 mocks.api.mockResolvedValue({enabled:true,clinician_username:'phaseclinician',admin_username:'phaseadmin'});
 mocks.demoCredentials.mockResolvedValue({username:'phaseclinician',password:'local-secret'});
 render(<MemoryRouter><Login/></MemoryRouter>);
 expect(screen.getByRole('heading',{name:'G One'})).toBeInTheDocument();
 expect(screen.getByRole('group',{name:'Sign-in area'})).toBeInTheDocument();
 expect(screen.getByText('phaseclinician')).toBeInTheDocument();
 expect(screen.getByText(/Administrator accounts cannot enter or change clinical records/)).toBeInTheDocument();
 const demoButton=await screen.findByRole('button',{name:/Demo clinician phaseclinician Load username and password/});
 await waitFor(()=>expect(demoButton).toBeEnabled());
 fireEvent.click(demoButton);
 await waitFor(()=>expect(screen.getByLabelText('Username')).toHaveValue('phaseclinician'));
 expect(screen.getByLabelText('Password')).toHaveValue('local-secret');
 expect(mocks.demoCredentials).toHaveBeenCalledWith('clinician');
 expect(screen.getByRole('status')).toHaveTextContent('Demo clinician username and password loaded');
});

test('switches the sign-in context without assigning account permissions',()=>{
 mocks.api.mockResolvedValue({enabled:false});
 render(<MemoryRouter><Login/></MemoryRouter>);
 fireEvent.click(screen.getByRole('button',{name:'Administration'}));
 expect(screen.getByRole('button',{name:'Sign in to administration'})).toBeInTheDocument();
 expect(screen.getByText('Access is determined by your account permissions.')).toBeInTheDocument();
});

test('administrator demo tile fetches and fills its login details',async()=>{
 mocks.api.mockResolvedValue({enabled:true,clinician_username:'phaseclinician',admin_username:'phaseadmin'});
 mocks.demoCredentials.mockResolvedValue({username:'phaseadmin',password:'admin-local-secret'});
 render(<MemoryRouter><Login/></MemoryRouter>);
 const adminTile=await screen.findByRole('button',{name:/Administrator phaseadmin Load username and password/});
 await waitFor(()=>expect(adminTile).toHaveTextContent('Load username and password'));
 await waitFor(()=>expect(adminTile).toBeEnabled());
 fireEvent.click(adminTile);
 await waitFor(()=>expect(screen.getByLabelText('Username')).toHaveValue('phaseadmin'));
 expect(screen.getByLabelText('Password')).toHaveValue('admin-local-secret');
 expect(mocks.demoCredentials).toHaveBeenCalledWith('admin');
});

test('account tiles fill the username when local demo sign-in is disabled',async()=>{
 mocks.api.mockResolvedValue({enabled:false,clinician_username:'phaseclinician',admin_username:'phaseadmin'});
 render(<MemoryRouter><Login/></MemoryRouter>);
 const adminTile=screen.getByRole('button',{name:/Administrator phaseadmin/});
 await waitFor(()=>expect(adminTile).toBeEnabled());
 fireEvent.click(adminTile);
 expect(screen.getByLabelText('Username')).toHaveValue('phaseadmin');
 expect(screen.getByLabelText('Password')).toHaveValue('');
 expect(screen.getByRole('button',{name:'Sign in to administration'})).toBeInTheDocument();
 expect(mocks.demoCredentials).not.toHaveBeenCalled();
});
