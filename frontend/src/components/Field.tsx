import type {InputHTMLAttributes} from 'react';
export function Field({label,id,...props}:InputHTMLAttributes<HTMLInputElement>&{label:string;id:string}){return <label className="field" htmlFor={id}>{label}<input id={id} {...props}/></label>}
