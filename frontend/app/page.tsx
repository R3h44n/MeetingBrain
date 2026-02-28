'use client';

import { useAudioStream } from '@/hooks/useAudioStream';
import ActionItemList from '@/components/ActionItemList';

export default function Home() {
  // Connect to the local FastAPI backend
  const { isRecording, startRecording, stopRecording, transcript, actionItems } = 
    useAudioStream('ws://localhost:8000/ws');

  return (
    <main className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <header className="mb-8 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-blue-600">MeetingBrain</h1>
          
          {/* The Pulsing Recording Indicator */}
          {isRecording && (
            <div className="flex items-center gap-2 px-3 py-1 bg-red-50 rounded-full border border-red-100">
              <span className="relative flex h-3 w-3">
                {/* The pinging background layer */}
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                {/* The solid core dot */}
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
              <span className="text-sm font-medium text-red-600 animate-pulse">
                Recording
              </span>
            </div>
          )}
        </div>

        <button 
          onClick={isRecording ? stopRecording : startRecording}
          className={`px-6 py-3 rounded-full font-semibold text-white transition-colors shadow-sm ${
            isRecording 
              ? 'bg-red-500 hover:bg-red-600 focus:ring-4 focus:ring-red-200' 
              : 'bg-green-500 hover:bg-green-600 focus:ring-4 focus:ring-green-200'
          }`}
        >
          {isRecording ? 'Stop Meeting' : 'Start Meeting'}
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 h-[80vh]">
        {/* Left Column: Live Transcript */}
        <section className="col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col">
          <h2 className="text-xl font-semibold border-b pb-4 mb-4">Live Transcript</h2>
          <div className="flex-1 overflow-y-auto font-mono text-sm text-gray-700 whitespace-pre-wrap">
            {transcript || "Waiting for conversation to start..."}
          </div>
        </section>

        {/* Right Column: AI Action Items */}
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col">
          <div className="flex items-center gap-2 border-b pb-4 mb-4">
            <h2 className="text-xl font-semibold text-indigo-600">Action Items</h2>
            {/* Dynamic Badge showing the number of tasks extracted */}
            {actionItems.length > 0 && (
              <span className="bg-indigo-100 text-indigo-700 text-xs py-1 px-2 rounded-full font-bold">
                {actionItems.length}
              </span>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {/* Dropping in your new dedicated component */}
            <ActionItemList items={actionItems} />
          </div>
        </section>
      </div>
    </main>
  );
}