import ReceptionEntry from '@/components/reception-entry';
import {requireChatGPTUser} from '@/app/chatgpt-auth';
export const dynamic='force-dynamic';
export const metadata={title:'三宮を呼び出す｜オールマイティ',manifest:'/call.webmanifest',appleWebApp:{capable:false,title:'三宮を呼ぶ'},icons:{icon:'/call-icon.png',apple:'/call-icon.png'}};
async function Authorized(){await requireChatGPTUser('/');return <ReceptionEntry/>}
export default function Home(){return <Authorized/>}
