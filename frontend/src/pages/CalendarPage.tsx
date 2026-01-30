/**
 * TB Personal OS - Calendar Page
 */

import React, { useEffect, useState } from 'react';
import { 
  Calendar as CalendarIcon, 
  ChevronLeft, 
  ChevronRight,
  Plus,
  Clock,
  MapPin,
  RefreshCw,
  AlertCircle,
  Video
} from 'lucide-react';
import { Card, CardTitle, CardContent, Button } from '../components/ui';
import { api } from '../services/api';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, addMonths, subMonths, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface CalendarEvent {
  id: string;
  summary: string;
  start: { dateTime?: string; date?: string };
  end: { dateTime?: string; date?: string };
  location?: string;
  description?: string;
  hangoutLink?: string;
}

export const CalendarPage: React.FC = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    checkConnection();
  }, []);

  useEffect(() => {
    if (isConnected) {
      loadEvents();
    }
  }, [currentDate, isConnected]);

  const checkConnection = async () => {
    try {
      const status = await api.get('/auth/google/status');
      setIsConnected(status.connected);
      if (!status.connected) {
        setIsLoading(false);
      }
    } catch {
      setIsConnected(false);
      setIsLoading(false);
    }
  };

  const loadEvents = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const start = startOfMonth(currentDate);
      const end = endOfMonth(currentDate);
      
      const data = await api.get('/calendar/events', {
        params: {
          start_date: start.toISOString(),
          end_date: end.toISOString(),
        }
      });

      setEvents(data || []);
    } catch (err: any) {
      setError('Erro ao carregar eventos');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const { auth_url } = await api.get('/auth/google/authorize');
      window.location.href = auth_url;
    } catch (err) {
      setError('Erro ao iniciar conexão');
    }
  };

  const getDaysInMonth = () => {
    const start = startOfMonth(currentDate);
    const end = endOfMonth(currentDate);
    return eachDayOfInterval({ start, end });
  };

  const getEventsForDay = (day: Date) => {
    return events.filter(event => {
      const eventDate = event.start.dateTime 
        ? parseISO(event.start.dateTime)
        : event.start.date 
          ? parseISO(event.start.date)
          : null;
      return eventDate && isSameDay(eventDate, day);
    });
  };

  const formatEventTime = (event: CalendarEvent) => {
    if (event.start.dateTime) {
      return format(parseISO(event.start.dateTime), 'HH:mm');
    }
    return 'Dia inteiro';
  };

  const days = getDaysInMonth();
  const firstDayOfMonth = startOfMonth(currentDate).getDay();
  const selectedDayEvents = selectedDate ? getEventsForDay(selectedDate) : [];

  if (!isConnected) {
    return (
      <div className="p-6">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-8 text-center">
            <CalendarIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Conecte seu Google Calendar
            </h2>
            <p className="text-gray-500 mb-6">
              Para ver seus eventos, conecte sua conta Google.
            </p>
            <Button onClick={handleConnect}>
              Conectar Google
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <CalendarIcon className="w-7 h-7 text-blue-500" />
            Agenda
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Seus eventos do Google Calendar
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={loadEvents} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
          <Button size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Novo Evento
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-400">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar Grid */}
        <Card className="lg:col-span-2">
          <CardContent className="p-4">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => setCurrentDate(subMonths(currentDate, 1))}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                {format(currentDate, 'MMMM yyyy', { locale: ptBR })}
              </h2>
              <button
                onClick={() => setCurrentDate(addMonths(currentDate, 1))}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Weekday Headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'].map(day => (
                <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Days */}
            <div className="grid grid-cols-7 gap-1">
              {/* Empty cells for days before month starts */}
              {Array.from({ length: firstDayOfMonth }).map((_, i) => (
                <div key={`empty-${i}`} className="aspect-square" />
              ))}
              
              {/* Days of the month */}
              {days.map(day => {
                const dayEvents = getEventsForDay(day);
                const isToday = isSameDay(day, new Date());
                const isSelected = selectedDate && isSameDay(day, selectedDate);

                return (
                  <button
                    key={day.toISOString()}
                    onClick={() => setSelectedDate(day)}
                    className={`
                      aspect-square p-1 rounded-lg text-sm relative
                      ${isToday ? 'bg-blue-500 text-white' : ''}
                      ${isSelected && !isToday ? 'bg-blue-100 dark:bg-blue-900' : ''}
                      ${!isToday && !isSelected ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : ''}
                    `}
                  >
                    <span className="block">{format(day, 'd')}</span>
                    {dayEvents.length > 0 && (
                      <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2 flex gap-0.5">
                        {dayEvents.slice(0, 3).map((_, i) => (
                          <span 
                            key={i} 
                            className={`w-1.5 h-1.5 rounded-full ${isToday ? 'bg-white' : 'bg-blue-500'}`}
                          />
                        ))}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Selected Day Events */}
        <Card>
          <CardTitle className="p-4 border-b dark:border-gray-700">
            {selectedDate 
              ? format(selectedDate, "d 'de' MMMM", { locale: ptBR })
              : 'Selecione um dia'
            }
          </CardTitle>
          <CardContent className="p-4">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
              </div>
            ) : selectedDate ? (
              selectedDayEvents.length > 0 ? (
                <div className="space-y-3">
                  {selectedDayEvents.map(event => (
                    <div 
                      key={event.id}
                      className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-blue-500"
                    >
                      <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                        {event.summary}
                      </h4>
                      <div className="space-y-1 text-sm text-gray-500">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4" />
                          {formatEventTime(event)}
                        </div>
                        {event.location && (
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4" />
                            {event.location}
                          </div>
                        )}
                        {event.hangoutLink && (
                          <a 
                            href={event.hangoutLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-blue-500 hover:underline"
                          >
                            <Video className="w-4 h-4" />
                            Entrar na reunião
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-8">
                  Nenhum evento neste dia
                </p>
              )
            ) : (
              <p className="text-center text-gray-500 py-8">
                Clique em um dia para ver os eventos
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CalendarPage;
