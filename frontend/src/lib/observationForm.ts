import {z} from 'zod';

const optionalNumber=(min:number,max:number,label:string)=>z.string().optional().refine(value=>!value?.trim()||(Number.isFinite(Number(value))&&Number(value)>=min&&Number(value)<=max),`${label} is outside the technical entry range.`);
export const observationSchema=z.object({
 respiration_rate:optionalNumber(1,100,'Respiration rate'),
 spo2:optionalNumber(50,100,'Oxygen saturation'),
 supplemental_o2:z.enum(['','no','yes']).optional(),
 systolic_bp:optionalNumber(30,300,'Systolic blood pressure'),
 pulse:optionalNumber(20,300,'Pulse'),
 consciousness:z.enum(['','ALERT','NEW_CONFUSION','VOICE','PAIN','UNRESPONSIVE']).optional(),
 temperature:optionalNumber(25,45,'Temperature'),
}).superRefine((values,ctx)=>{
 if(!['respiration_rate','spo2','systolic_bp','pulse','consciousness','temperature'].some(key=>values[key as keyof typeof values]?.trim()))ctx.addIssue({code:'custom',message:'Enter at least one observation value.',path:['root']});
 if(values.spo2?.trim()&&!values.supplemental_o2)ctx.addIssue({code:'custom',message:'Select whether supplemental oxygen is in use when entering oxygen saturation.',path:['supplemental_o2']});
});
export type ObservationFormValues=z.infer<typeof observationSchema>;
export function observationFormError(values:Record<string,string>):string|undefined{
 const parsed=observationSchema.safeParse(values);
 return parsed.success?undefined:parsed.error.issues[0]?.message;
}
export function observationPayload(values:ObservationFormValues,admissionId:string,measuredAt:string,recordId:string){
 const fields=['respiration_rate','spo2','systolic_bp','pulse','consciousness','temperature'] as const;
 const payload:Record<string,unknown>={admission_id:admissionId,measured_at:measuredAt,source:'manual',source_record_id:recordId,is_simulated:true};
 for(const key of fields){const raw=values[key]?.trim();if(raw)payload[key]=key==='temperature'?raw:Number(raw)}
 if(values.spo2?.trim()||values.supplemental_o2)payload.supplemental_o2=values.supplemental_o2==='yes';
 return payload;
}