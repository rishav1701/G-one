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
 expect(screen.getByRole('heading',{name:'Demo access for judges'})).toBeInTheDocument();
 expect(screen.getByText(/For patient records, manual observations, and alert actions/)).toBeInTheDocument();
 expect(screen.getByText('phaseclinician')).toBeInTheDocument();
 expect(screen.getByText(/ADMIN is for demonstration controls and cannot enter clinical data/)).toBeInTheDocument();
 const button=await screen.findByRole('button',{name:'Continue as demo clinician'});
 fireEvent.click(button);
 await waitFor(()=>expect(mocks.demoLogin).toHaveBeenCalledOnce());
});
