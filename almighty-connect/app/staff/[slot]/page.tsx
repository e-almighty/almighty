import Desk from '@/components/desk';
import DeskBoundary from '@/components/desk-boundary';
import {requireChatGPTUser} from '@/app/chatgpt-auth';
import {notFound} from 'next/navigation';
export const dynamic='force-dynamic';
async function Authorized({slot}:{slot:string}){await requireChatGPTUser('/staff/'+slot);return <DeskBoundary><Desk device={{role:'staff',slot}}/></DeskBoundary>}
export default async function Page({params}:{params:Promise<{slot:string}>}){const {slot}=await params;if(!['1','2','3','4','5'].includes(slot))notFound();return <Authorized slot={slot}/>}
