import {fireEvent,render,screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {beforeEach,expect,test,vi} from 'vitest';

const mocks=vi.hoisted(()=>({login:vi.fn()}));
vi.mock('./Auth',()=>({useAuth:()=>({login:mocks.login})}));

import Login from './Login';

beforeEach(()=>vi.clearAllMocks());

test('loads the fixed clinician demo credentials immediately without an API request',()=>{
 render(<MemoryRouter><Login/></MemoryRouter>);
 expect(screen.getByRole('heading',{name:'G One'})).toBeInTheDocument();
 expect(screen.getByRole('group',{name:'Sign-in area'})).toBeInTheDocument();
 expect(screen.getByText('phaseclinician')).toBeInTheDocument();
 expect(screen.getByText(/Administrator accounts cannot enter or change clinical records/)).toBeInTheDocument();
 const demoButton=screen.getByRole('button',{name:/Demo clinician phaseclinician Load username and password/});
 expect(demoButton).toBeEnabled();
 fireEvent.click(demoButton);
 expect(screen.getByLabelText('Username')).toHaveValue('phaseclinician');
 expect(screen.getByLabelText('Password')).toHaveValue('clinical321');
 expect(screen.getByRole('status')).toHaveTextContent('Demo clinician username and password loaded');
});

test('switches the sign-in context without assigning account permissions',()=>{
 render(<MemoryRouter><Login/></MemoryRouter>);
 fireEvent.click(screen.getByRole('button',{name:'Administration'}));
 expect(screen.getByRole('button',{name:'Sign in to administration'})).toBeInTheDocument();
 expect(screen.getByText('Access is determined by your account permissions.')).toBeInTheDocument();
});

test('administrator demo tile immediately fills its fixed login details',()=>{
 render(<MemoryRouter><Login/></MemoryRouter>);
 const adminTile=screen.getByRole('button',{name:/Administrator phaseadmin Load username and password/});
 expect(adminTile).toBeEnabled();
 fireEvent.click(adminTile);
 expect(screen.getByLabelText('Username')).toHaveValue('phaseadmin');
 expect(screen.getByLabelText('Password')).toHaveValue('admin321');
 expect(screen.getByRole('button',{name:'Sign in to administration'})).toBeInTheDocument();
});
