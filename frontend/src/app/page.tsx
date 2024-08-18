"use client"
import React, { useState, useRef } from 'react'

import { cn } from "@/lib/utils"
import { CaretSortIcon, CheckIcon } from "@radix-ui/react-icons"
import { ExclamationTriangleIcon } from "@radix-ui/react-icons"
import { SendIcon, SettingsIcon, SGFlag, MSFlag, IDFlag } from "@/components/lib/icons"

import { addDays, format } from "date-fns"
import { DateRange } from "react-day-picker"


import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious
} from '@/components/ui/pagination'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { DatePickerWithRange } from "@/components/ui/date-range-picker"

const filters = [
  {
    value: "site",
    label: "site",
  },
  {
    value: "date",
    label: "date",
  }
]

type Location = "Singapore" | "Malaysia" | "Indonesia"

type Article = {
  url: string,
  title: string,
  content: string,
  language: string,
  location: Location,
  site: string,
  date: string,
}

const LocationToFlag = {
  "Singapore": <SGFlag />,
  "Malaysia": <MSFlag />,
  "Indonesia": <IDFlag />,
}

type TagCount = {
  tag: string,
  count: number
}

const API_URL: string = process.env.API_URL || 'http://localhost:8000';


export default function Home() {
  const [open, setOpen] = useState<boolean>(false);
  const [tags, setTags] = useState<TagCount[]>([]);
  const [value, setValue] = useState<string>("");
  const [date, setDate] = useState<DateRange | undefined>({from: new Date(2024, 1, 1), to: addDays(new Date(2024, 1, 1), 28)}); 
  const [sendHover, setSendHover] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [articleResults, setArticleResults] = useState<Article[]>([]);

  const urlRef = useRef<HTMLInputElement>(null);
  const filterRef = useRef<HTMLButtonElement>(null);
  const DateRef = useRef<HTMLInputElement>(null);

  // Pagination for card results
  const cardsPerPage = 3;
  const [startIndex, setStartIndex] = useState(0);

  const filterArticles = async () => {
    if (!urlRef.current || !filterRef.current) {
      setErrorMsg("URL or Filter cannot be empty!");
      return;
    }

    const urlValue = urlRef.current.value.trim();
    const rawFilterValue = filterRef.current.textContent as string;

    if (!filters.some(filter => rawFilterValue === `Filter by ${filter.value}`)) {
      setErrorMsg("Filter cannot be empty!");
      return;
    }

    setStartIndex(0);
    setErrorMsg("");


    const filterValue = rawFilterValue.split(' ').pop();
    const endpoint = `${API_URL}/filter/${filterValue}?${new URLSearchParams({ url: urlValue }).toString()}`;

    let retrievedArticles: Article[] = [];

    // Send GET request to the frontend
    try {
      const response = await fetch(endpoint,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });

      if (response.ok) {
        retrievedArticles = await response.json();

      } else {
        setErrorMsg("Failed to get response from the server");
      }
    } catch (err) {
      console.error("Error: ", err);
      setErrorMsg(`${err}`);
    }

    setArticleResults([...retrievedArticles]);
  }

  const getTopTags = async () => {
    // Get dates from the date picker
    const start_date = format(date?.from as Date, "yyyy-MM-dd");
    const end_date = format(date?.to as Date, "yyyy-MM-dd");

    const endpoint = `${API_URL}/tags?${new URLSearchParams({ start_date: start_date , end_date: end_date, top_n: "25" }).toString()}`;
    let retrievedTags: TagCount[] = [];

    try {
      const response = await fetch(endpoint,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });

      if (response.ok) {
        retrievedTags = await response.json() as TagCount[];
        setTags([...retrievedTags]);
      } else {
        setErrorMsg("Failed to get response from the server");
      }
    } catch (err) {
      console.error("Error: ", err);
      setErrorMsg(`${err}`);
    }

    return retrievedTags; 
  }


  return (
    <div className='flex flex-col w-full h-full'>
      <Tabs defaultValue="filter" className={`w-full ${articleResults.length > 0 ? 'h-auto' : 'h-full'}`}>
        <div className='flex w-full px-4 py-3 gap-x-3 justify-center'>
          <TabsList className="">
            <TabsTrigger value="filter" onClick={() => { setArticleResults([]); setErrorMsg(''); setTags([]); }}>Filter Similar Articles</TabsTrigger>
            <TabsTrigger value="top_tags" onClick={() => { setArticleResults([]); setErrorMsg(''); setTags([]); }}>Get Top Tags</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="filter" className={`${articleResults.length > 0 ? 'h-auto' : ''}`}>
          <div className='flex w-full px-4 pb-3 gap-x-3 justify-center items-center'>
            <SettingsIcon className='align-middle h-full' />
            <Input type='search' className='bg-[#262730] border-none w-[35rem] pl-9' placeholder='Enter URL here' ref={urlRef}></Input>
            <Popover open={open} onOpenChange={setOpen}>
              <PopoverTrigger asChild>
                <Button ref={filterRef} variant="outline" role="combobox" aria-expanded={open} className="w-52 justify-between bg-[#262730] border-none hover:bg-[#262730] hover:text-[#ffffff]">
                  {value ? `Filter by ${filters.find((filtered) => filtered.value === value)?.label}` : "Select Filter..."}
                  <CaretSortIcon className='ml-2 h-4 w-4 shrink-0 opacity-50' />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-52 p-0 border-[#a75adb] border-4 rounded-xl">
                <Command className='bg-[#0e1117] text-[#ffffff] border-none'>
                  <CommandInput placeholder="Search Filter..." className='h-9 bg-[#0e1117]' />
                  <CommandEmpty>No Filter Found</CommandEmpty>
                  <CommandGroup>
                    <CommandList>
                      {filters && filters.map((filtered) =>
                      (
                        <CommandItem
                          className='text-[#ffffff] bg-[#0e1117] capitalize'
                          key={filtered.value}
                          value={filtered.value}
                          onSelect={(currentValue) => {
                            setValue(currentValue === value ? "" : currentValue)
                            setOpen(false)
                          }}
                        >
                          {filtered.label}
                          <CheckIcon
                            className={cn(
                              "ml-auto h-4 w-4",
                              value === filtered.value ? "opacity-100" : "opacity-0"
                            )}
                          />
                        </CommandItem>
                      ))}
                    </CommandList>
                  </CommandGroup>
                </Command>
              </PopoverContent>
            </Popover>
            <Button variant="default" className="bg-[#262730] hover:bg-[#262730]" onMouseEnter={() => setSendHover(true)} onMouseLeave={() => setSendHover(false)} onClick={() => filterArticles()}>
              <SendIcon className="" color={sendHover ? "#a75adb" : "#ffffff"} />
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="top_tags">
          <div className='flex w-full px-4 pb-3 gap-x-3 justify-center items-center'>
            <SettingsIcon className={`align-middle h-full ${tags.length > 0 ? 'self-end pb-2' : ''}`} />
            <DatePickerWithRange className='bg-[#262730]' date={date} setDate={setDate}  />
            <Button variant="default" className={`bg-[#262730] hover:bg-[#262730] ${tags.length > 0 ? 'self-end' : ''}`} onMouseEnter={() => setSendHover(true)} onMouseLeave={() => setSendHover(false)} onClick={() => getTopTags()}>
              <SendIcon className="" color={sendHover ? "#a75adb" : "#ffffff"} />
            </Button>
          </div>
        </TabsContent>
      </Tabs>

      <div className={`flex w-full h-full ${errorMsg === "" ? "" : "justify-start"}`}>
        {errorMsg === "" ?
          articleResults.length > 0 ? <div className='flex flex-col h-full w-full mt-4'>
            <div className='flex justify-evenly w-full h-[85%]'>
              {articleResults.slice(startIndex, startIndex + cardsPerPage).map((article, idx) => (
                <Card className="w-96 max-h-96 mt-4 mb-2 flex flex-col bg-[#dfdfdf]" key={idx}>
                  <CardHeader>
                    <CardTitle className="text-lg">{article.title}</CardTitle>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger className='w-12'>
                          {LocationToFlag[article.location]}
                        </TooltipTrigger>
                        <TooltipContent side='right'>
                          <p>{article.location}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <CardDescription>{article.site} | {article.date} | {article.language}</CardDescription>
                  </CardHeader>
                  <CardContent className="overflow-hidden">
                    <div
                      className="overflow-hidden text-ellipsis"
                      style={{
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical'
                      }}
                    >
                      {article.content}
                    </div>
                  </CardContent>
                  <CardFooter className='pb-4 mt-auto'>
                    <div className="flex whitespace-nowrap w-full">View more: &nbsp;<a href={article.url} className="max-w-[75%]" target="_blank"><p className="overflow-hidden text-ellipsis text-[#bd6bf4] hover:underline">{article.url}</p></a></div>
                  </CardFooter>
                </Card>
              ))}
            </div>
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious className={`select-none
                    ${startIndex === 0 ? "pointer-events-none opacity-50" : undefined}
                  `} onClick={() => {
                      setStartIndex(startIndex - cardsPerPage);
                    }} />
                </PaginationItem>

                <PaginationItem>
                  <PaginationLink className='select-none'>
                    {Math.ceil(startIndex / cardsPerPage) + 1}/{Math.ceil(articleResults.length / cardsPerPage)}
                  </PaginationLink>
                </PaginationItem>

                <PaginationItem>
                  <PaginationNext className={`select-none
                    ${startIndex + cardsPerPage >= articleResults.length ? "pointer-events-none opacity-50" : undefined}
                  `} onClick={() => {
                      setStartIndex(startIndex + cardsPerPage);
                    }} />
                </PaginationItem>

              </PaginationContent>
            </Pagination>
          </div>
          :
          
          tags.length > 0 && 
          <div className='flex w-full'>
          <Table className='w-1/2 mx-auto'>
            <TableCaption>List of Tags</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-92">Tags</TableHead>
                <TableHead className="text-right">Count</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {
              tags.map(({tag, count}, idx) => (
                 <TableRow key={idx}>
                    <TableCell>{tag}</TableCell>
                    <TableCell className="text-right">{count}</TableCell>
                  </TableRow> 
              ))
              }
            </TableBody>
          </Table>
          </div>

          :
          <Alert variant="destructive" className='w-[32rem] h-20 mx-auto mt-4'>
            <ExclamationTriangleIcon className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {errorMsg}
            </AlertDescription>
          </Alert>
        }
      </div>
    </div >
  )
}

