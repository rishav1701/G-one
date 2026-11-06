import {Navigate,Outlet} from 'react-router-dom';import {useAuth} from './Auth';
export function RequireAuth(){const{user,loading}=useAuth();if(loading)return <div role="status">Loading session…</div>;return user?<Outlet/>:<Navigate to="/login" replace/>}
