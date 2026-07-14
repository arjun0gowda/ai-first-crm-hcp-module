import {createAsyncThunk,createSlice} from '@reduxjs/toolkit'; import {api} from '../api';
export const fetchHcps=createAsyncThunk('i/hcps',async()=> (await api.get('/hcps')).data);
export const fetchInteractions=createAsyncThunk('i/list',async()=> (await api.get('/interactions?limit=10')).data);
export const submitInteraction=createAsyncThunk('i/submit',async(p,{rejectWithValue})=>{try{return (await api.post('/interactions',p)).data}catch(e){return rejectWithValue(e.response?.data?.detail||e.message)}});
const initial={hcps:[],items:[],status:'idle',error:null,draft:null,lastCreated:null};
const slice=createSlice({name:'interactions',initialState:initial,reducers:{populateDraft:(s,a)=>{s.draft=a.payload},clearDraft:s=>{s.draft=null}},extraReducers:b=>b.addCase(fetchHcps.fulfilled,(s,a)=>{s.hcps=a.payload}).addCase(fetchInteractions.fulfilled,(s,a)=>{s.items=a.payload}).addCase(submitInteraction.pending,s=>{s.status='loading';s.error=null}).addCase(submitInteraction.fulfilled,(s,a)=>{s.status='idle';s.lastCreated=a.payload;s.items.unshift(a.payload)}).addCase(submitInteraction.rejected,(s,a)=>{s.status='idle';s.error=a.payload})});
export const {populateDraft,clearDraft}=slice.actions; export default slice.reducer;
