import {AlertCircle,CheckCircle2,MinusCircle,AlertTriangle} from 'lucide-react';
const levelStyle={LOW:'low',LOW_MEDIUM:'low-medium',MEDIUM:'medium',HIGH:'high',INCOMPLETE:'incomplete',STALE:'stale',NO_DATA:'stale'} as const;
const icons={LOW:CheckCircle2,LOW_MEDIUM:AlertTriangle,MEDIUM:AlertTriangle,HIGH:AlertCircle,INCOMPLETE:MinusCircle,STALE:MinusCircle,NO_DATA:MinusCircle} as const;
export type Level=keyof typeof levelStyle;
export function LevelBadge({level}:{level:Level}){const Icon=icons[level];return <span className={`badge badge-${levelStyle[level]}`}><Icon aria-hidden="true" size={14}/><span>{level==='INCOMPLETE'?'Assessment limited':level.replace('_',' ')}</span></span>}
